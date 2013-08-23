# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010-2012 OpenStack LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
TOKEN-BASED AUTH MIDDLEWARE

This WSGI component:

* Verifies that incoming client requests have valid tokens by validating
  tokens with the auth service.
* Rejects unauthenticated requests UNLESS it is in 'delay_auth_decision'
  mode, which means the final decision is delegated to the downstream WSGI
  component (usually the OpenStack service)
* Collects and forwards identity information based on a valid token
  such as user name, tenant, etc

Refer to: http://keystone.openstack.org/middlewarearchitecture.html

HEADERS
-------

* Headers starting with HTTP\_ is a standard http header
* Headers starting with HTTP_X is an extended http header

Coming in from initial call from client or customer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

HTTP_X_AUTH_TOKEN
    The client token being passed in.

HTTP_X_STORAGE_TOKEN
    The client token being passed in (legacy Rackspace use) to support
    swift/cloud files

Used for communication between components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

WWW-Authenticate
    HTTP header returned to a user indicating which endpoint to use
    to retrieve a new token

What we add to the request for use by the OpenStack service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

HTTP_X_IDENTITY_STATUS
    'Confirmed' or 'Invalid'
    The underlying service will only see a value of 'Invalid' if the Middleware
    is configured to run in 'delay_auth_decision' mode

HTTP_X_DOMAIN_ID
    Identity service managed unique identifier, string. Only present if
    this is a domain-scoped v3 token.

HTTP_X_DOMAIN_NAME
    Unique domain name, string. Only present if this is a domain-scoped
    v3 token.

HTTP_X_PROJECT_ID
    Identity service managed unique identifier, string. Only present if
    this is a project-scoped v3 token, or a tenant-scoped v2 token.

HTTP_X_PROJECT_NAME
    Project name, unique within owning domain, string. Only present if
    this is a project-scoped v3 token, or a tenant-scoped v2 token.

HTTP_X_PROJECT_DOMAIN_ID
    Identity service managed unique identifier of owning domain of
    project, string.  Only present if this is a project-scoped v3 token. If
    this variable is set, this indicates that the PROJECT_NAME can only
    be assumed to be unique within this domain.

HTTP_X_PROJECT_DOMAIN_NAME
    Name of owning domain of project, string. Only present if this is a
    project-scoped v3 token. If this variable is set, this indicates that
    the PROJECT_NAME can only be assumed to be unique within this domain.

HTTP_X_USER_ID
    Identity-service managed unique identifier, string

HTTP_X_USER_NAME
    User identifier, unique within owning domain, string

HTTP_X_USER_DOMAIN_ID
    Identity service managed unique identifier of owning domain of
    user, string. If this variable is set, this indicates that the USER_NAME
    can only be assumed to be unique within this domain.

HTTP_X_USER_DOMAIN_NAME
    Name of owning domain of user, string. If this variable is set, this
    indicates that the USER_NAME can only be assumed to be unique within
    this domain.

HTTP_X_ROLES
    Comma delimited list of case-sensitive role names

HTTP_X_SERVICE_CATALOG
    json encoded keystone service catalog (optional).

HTTP_X_TENANT_ID
    *Deprecated* in favor of HTTP_X_PROJECT_ID
    Identity service managed unique identifier, string. For v3 tokens, this
    will be set to the same value as HTTP_X_PROJECT_ID

HTTP_X_TENANT_NAME
    *Deprecated* in favor of HTTP_X_PROJECT_NAME
    Project identifier, unique within owning domain, string. For v3 tokens,
    this will be set to the same value as HTTP_X_PROJECT_NAME

HTTP_X_TENANT
    *Deprecated* in favor of HTTP_X_TENANT_ID and HTTP_X_TENANT_NAME
    Keystone-assigned unique identifier, string. For v3 tokens, this
    will be set to the same value as HTTP_X_PROJECT_ID

HTTP_X_USER
    *Deprecated* in favor of HTTP_X_USER_ID and HTTP_X_USER_NAME
    User name, unique within owning domain, string

HTTP_X_ROLE
    *Deprecated* in favor of HTTP_X_ROLES
    Will contain the same values as HTTP_X_ROLES.

OTHER ENVIRONMENT VARIABLES
---------------------------

keystone.token_info
    Information about the token discovered in the process of
    validation.  This may include extended information returned by the
    Keystone token validation call, as well as basic information about
    the tenant and user.

"""

import datetime
import httplib
import json
import logging
import os
import stat
import tempfile
import time
import urllib

import six

from keystoneclient.common import cms
from keystoneclient.middleware import memcache_crypt
from keystoneclient.openstack.common import jsonutils
from keystoneclient.openstack.common import memorycache
from keystoneclient.openstack.common import timeutils
from keystoneclient import utils

CONF = None
# to pass gate before oslo-config is deployed everywhere,
# try application copies first
for app in 'nova', 'glance', 'quantum', 'cinder':
    try:
        cfg = __import__('%s.openstack.common.cfg' % app,
                         fromlist=['%s.openstack.common' % app])
        # test which application middleware is running in
        if hasattr(cfg, 'CONF') and 'config_file' in cfg.CONF:
            CONF = cfg.CONF
            break
    except ImportError:
        pass
if not CONF:
    from oslo.config import cfg
    CONF = cfg.CONF

# alternative middleware configuration in the main application's
# configuration file e.g. in nova.conf
# [keystone_authtoken]
# auth_host = 127.0.0.1
# auth_port = 35357
# auth_protocol = http
# admin_tenant_name = admin
# admin_user = admin
# admin_password = badpassword

# when deploy Keystone auth_token middleware with Swift, user may elect
# to use Swift memcache instead of the local Keystone memcache. Swift memcache
# is passed in from the request environment and its identified by the
# 'swift.cache' key. However it could be different, depending on deployment.
# To use Swift memcache, you must set the 'cache' option to the environment
# key where the Swift cache object is stored.
opts = [
    cfg.StrOpt('auth_admin_prefix',
               default='',
               help='Prefix to prepend at the beginning of the path'),
    cfg.StrOpt('auth_host',
               default='127.0.0.1',
               help='Host providing the admin Identity API endpoint'),
    cfg.IntOpt('auth_port',
               default=35357,
               help='Port of the admin Identity API endpoint'),
    cfg.StrOpt('auth_protocol',
               default='https',
               help='Protocol of the admin Identity API endpoint'
               '(http or https)'),
    cfg.StrOpt('auth_uri',
               default=None,
               # FIXME(dolph): should be default='http://127.0.0.1:5000/v2.0/',
               # or (depending on client support) an unversioned, publicly
               # accessible identity endpoint (see bug 1207517)
               help='Complete public Identity API endpoint'),
    cfg.StrOpt('auth_version',
               default=None,
               help='API version of the admin Identity API endpoint'),
    cfg.BoolOpt('delay_auth_decision',
                default=False,
                help='Do not handle authorization requests within the'
                ' middleware, but delegate the authorization decision to'
                ' downstream WSGI components'),
    cfg.BoolOpt('http_connect_timeout',
                default=None,
                help='Request timeout value for communicating with Identity'
                ' API server.'),
    cfg.IntOpt('http_request_max_retries',
               default=3,
               help='How many times are we trying to reconnect when'
               ' communicating with Identity API Server.'),
    cfg.StrOpt('http_handler',
               default=None,
               help='Allows to pass in the name of a fake http_handler'
               ' callback function used instead of httplib.HTTPConnection or'
               ' httplib.HTTPSConnection. Useful for unit testing where'
               ' network is not available.'),
    cfg.StrOpt('admin_token',
               secret=True,
               help='Single shared secret with the Keystone configuration'
               ' used for bootstrapping a Keystone installation, or otherwise'
               ' bypassing the normal authentication process.'),
    cfg.StrOpt('admin_user',
               help='Keystone account username'),
    cfg.StrOpt('admin_password',
               secret=True,
               help='Keystone account password'),
    cfg.StrOpt('admin_tenant_name',
               default='admin',
               help='Keystone service account tenant name to validate'
               ' user tokens'),
    cfg.StrOpt('cache',
               default=None,
               help='Env key for the swift cache'),
    cfg.StrOpt('certfile',
               help='Required if Keystone server requires client certificate'),
    cfg.StrOpt('keyfile',
               help='Required if Keystone server requires client certificate'),
    cfg.StrOpt('signing_dir',
               help='Directory used to cache files related to PKI tokens'),
    cfg.ListOpt('memcached_servers',
                deprecated_name='memcache_servers',
                help='If defined, the memcache server(s) to use for'
                ' caching'),
    cfg.IntOpt('token_cache_time',
               default=300,
               help='In order to prevent excessive requests and validations,'
               ' the middleware uses an in-memory cache for the tokens the'
               ' Keystone API returns. This is only valid if memcache_servers'
               ' is defined. Set to -1 to disable caching completely.'),
    cfg.IntOpt('revocation_cache_time',
               default=1,
               help='Value only used for unit testing'),
    cfg.StrOpt('memcache_security_strategy',
               default=None,
               help='(optional) if defined, indicate whether token data'
               ' should be authenticated or authenticated and encrypted.'
               ' Acceptable values are MAC or ENCRYPT.  If MAC, token data is'
               ' authenticated (with HMAC) in the cache. If ENCRYPT, token'
               ' data is encrypted and authenticated in the cache. If the'
               ' value is not one of these options or empty, auth_token will'
               ' raise an exception on initialization.'),
    cfg.StrOpt('memcache_secret_key',
               default=None,
               secret=True,
               help='(optional, mandatory if memcache_security_strategy is'
               ' defined) this string is used for key derivation.')
]
CONF.register_opts(opts, group='keystone_authtoken')

LIST_OF_VERSIONS_TO_ATTEMPT = ['v2.0', 'v3.0']
CACHE_KEY_TEMPLATE = 'tokens/%s'


def will_expire_soon(expiry):
    """Determines if expiration is about to occur.

    :param expiry: a datetime of the expected expiration
    :returns: boolean : true if expiration is within 30 seconds
    """
    soon = (timeutils.utcnow() + datetime.timedelta(seconds=30))
    return expiry < soon


def safe_quote(s):
    """URL-encode strings that are not already URL-encoded."""
    return urllib.quote(s) if s == urllib.unquote(s) else s


class InvalidUserToken(Exception):
    pass


class ServiceError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class NetworkError(Exception):
    pass


class MiniResp(object):
    def __init__(self, error_message, env, headers=[]):
        # The HEAD method is unique: it must never return a body, even if
        # it reports an error (RFC-2616 clause 9.4). We relieve callers
        # from varying the error responses depending on the method.
        if env['REQUEST_METHOD'] == 'HEAD':
            self.body = ['']
        else:
            self.body = [error_message]
        self.headers = list(headers)
        self.headers.append(('Content-type', 'text/plain'))


class AuthProtocol(object):
    """Auth Middleware that handles authenticating client calls."""

    def __init__(self, app, conf):
        self.LOG = logging.getLogger(conf.get('log_name', __name__))
        self.LOG.info('Starting keystone auth_token middleware')
        self.conf = conf
        self.app = app

        # delay_auth_decision means we still allow unauthenticated requests
        # through and we let the downstream service make the final decision
        self.delay_auth_decision = (self._conf_get('delay_auth_decision') in
                                    (True, 'true', 't', '1', 'on', 'yes', 'y'))

        # where to find the auth service (we use this to validate tokens)
        self.auth_host = self._conf_get('auth_host')
        self.auth_port = int(self._conf_get('auth_port'))
        self.auth_protocol = self._conf_get('auth_protocol')
        if not self._conf_get('http_handler'):
            if self.auth_protocol == 'http':
                self.http_client_class = httplib.HTTPConnection
            else:
                self.http_client_class = httplib.HTTPSConnection
        else:
            # Really only used for unit testing, since we need to
            # have a fake handler set up before we issue an http
            # request to get the list of versions supported by the
            # server at the end of this initialization
            self.http_client_class = self._conf_get('http_handler')

        self.auth_admin_prefix = self._conf_get('auth_admin_prefix')
        self.auth_uri = self._conf_get('auth_uri')
        if self.auth_uri is None:
            self.LOG.warning(
                'Configuring auth_uri to point to the public identity '
                'endpoint is required; clients may not be able to '
                'authenticate against an admin endpoint')

            # FIXME(dolph): drop support for this fallback behavior as
            # documented in bug 1207517
            self.auth_uri = '%s://%s:%s' % (self.auth_protocol,
                                            self.auth_host,
                                            self.auth_port)

        # SSL
        self.cert_file = self._conf_get('certfile')
        self.key_file = self._conf_get('keyfile')

        # signing
        self.signing_dirname = self._conf_get('signing_dir')
        if self.signing_dirname is None:
            self.signing_dirname = tempfile.mkdtemp(prefix='keystone-signing-')
        self.LOG.info('Using %s as cache directory for signing certificate' %
                      self.signing_dirname)
        self.verify_signing_dir()

        val = '%s/signing_cert.pem' % self.signing_dirname
        self.signing_cert_file_name = val
        val = '%s/cacert.pem' % self.signing_dirname
        self.ca_file_name = val
        val = '%s/revoked.pem' % self.signing_dirname
        self.revoked_file_name = val

        # Credentials used to verify this component with the Auth service since
        # validating tokens is a privileged call
        self.admin_token = self._conf_get('admin_token')
        self.admin_token_expiry = None
        self.admin_user = self._conf_get('admin_user')
        self.admin_password = self._conf_get('admin_password')
        self.admin_tenant_name = self._conf_get('admin_tenant_name')

        # Token caching via memcache
        self._cache = None
        self._cache_initialized = False    # cache already initialzied?
        # memcache value treatment, ENCRYPT or MAC
        self._memcache_security_strategy = \
            self._conf_get('memcache_security_strategy')
        if self._memcache_security_strategy is not None:
            self._memcache_security_strategy = \
                self._memcache_security_strategy.upper()
        self._memcache_secret_key = \
            self._conf_get('memcache_secret_key')
        self._assert_valid_memcache_protection_config()
        # By default the token will be cached for 5 minutes
        self.token_cache_time = int(self._conf_get('token_cache_time'))
        self._token_revocation_list = None
        self._token_revocation_list_fetched_time = None
        self.token_revocation_list_cache_timeout = datetime.timedelta(
            seconds=self._conf_get('revocation_cache_time'))
        http_connect_timeout_cfg = self._conf_get('http_connect_timeout')
        self.http_connect_timeout = (http_connect_timeout_cfg and
                                     int(http_connect_timeout_cfg))
        self.auth_version = None
        self.http_request_max_retries = \
            self._conf_get('http_request_max_retries')

    def _assert_valid_memcache_protection_config(self):
        if self._memcache_security_strategy:
            if self._memcache_security_strategy not in ('MAC', 'ENCRYPT'):
                raise Exception('memcache_security_strategy must be '
                                'ENCRYPT or MAC')
            if not self._memcache_secret_key:
                raise Exception('mecmache_secret_key must be defined when '
                                'a memcache_security_strategy is defined')

    def _init_cache(self, env):
        cache = self._conf_get('cache')
        memcache_servers = self._conf_get('memcached_servers')

        if cache and env.get(cache, None) is not None:
            # use the cache from the upstream filter
            self.LOG.info('Using %s memcache for caching token', cache)
            self._cache = env.get(cache)
        else:
            # use Keystone memcache
            self._cache = memorycache.get_client(memcache_servers)
        self._cache_initialized = True

    def _conf_get(self, name):
        # try config from paste-deploy first
        if name in self.conf:
            return self.conf[name]
        else:
            return CONF.keystone_authtoken[name]

    def _choose_api_version(self):
        """Determine the api version that we should use."""

        # If the configuration specifies an auth_version we will just
        # assume that is correct and use it.  We could, of course, check
        # that this version is supported by the server, but in case
        # there are some problems in the field, we want as little code
        # as possible in the way of letting auth_token talk to the
        # server.
        if self._conf_get('auth_version'):
            version_to_use = self._conf_get('auth_version')
            self.LOG.info('Auth Token proceeding with requested %s apis',
                          version_to_use)
        else:
            version_to_use = None
            versions_supported_by_server = self._get_supported_versions()
            if versions_supported_by_server:
                for version in LIST_OF_VERSIONS_TO_ATTEMPT:
                    if version in versions_supported_by_server:
                        version_to_use = version
                        break
            if version_to_use:
                self.LOG.info('Auth Token confirmed use of %s apis',
                              version_to_use)
            else:
                self.LOG.error(
                    'Attempted versions [%s] not in list supported by '
                    'server [%s]',
                    ', '.join(LIST_OF_VERSIONS_TO_ATTEMPT),
                    ', '.join(versions_supported_by_server))
                raise ServiceError('No compatible apis supported by server')
        return version_to_use

    def _get_supported_versions(self):
        versions = []
        response, data = self._json_request('GET', '/')
        if response.status == 501:
            self.LOG.warning("Old keystone installation found...assuming v2.0")
            versions.append("v2.0")
        elif response.status != 300:
            self.LOG.error('Unable to get version info from keystone: %s' %
                           response.status)
            raise ServiceError('Unable to get version info from keystone')
        else:
            try:
                for version in data['versions']['values']:
                    versions.append(version['id'])
            except KeyError:
                self.LOG.error(
                    'Invalid version response format from server', data)
                raise ServiceError('Unable to parse version response '
                                   'from keystone')

        self.LOG.debug('Server reports support for api versions: %s',
                       ', '.join(versions))
        return versions

    def __call__(self, env, start_response):
        """Handle incoming request.

        Authenticate send downstream on success. Reject request if
        we can't authenticate.

        """
        self.LOG.debug('Authenticating user token')

        # initialize memcache if we haven't done so
        if not self._cache_initialized:
            self._init_cache(env)

        try:
            self._remove_auth_headers(env)
            user_token = self._get_user_token_from_header(env)
            token_info = self._validate_user_token(user_token)
            env['keystone.token_info'] = token_info
            user_headers = self._build_user_headers(token_info)
            self._add_headers(env, user_headers)
            return self.app(env, start_response)

        except InvalidUserToken:
            if self.delay_auth_decision:
                self.LOG.info(
                    'Invalid user token - deferring reject downstream')
                self._add_headers(env, {'X-Identity-Status': 'Invalid'})
                return self.app(env, start_response)
            else:
                self.LOG.info('Invalid user token - rejecting request')
                return self._reject_request(env, start_response)

        except ServiceError as e:
            self.LOG.critical('Unable to obtain admin token: %s' % e)
            resp = MiniResp('Service unavailable', env)
            start_response('503 Service Unavailable', resp.headers)
            return resp.body

    def _remove_auth_headers(self, env):
        """Remove headers so a user can't fake authentication.

        :param env: wsgi request environment

        """
        auth_headers = (
            'X-Identity-Status',
            'X-Domain-Id',
            'X-Domain-Name',
            'X-Project-Id',
            'X-Project-Name',
            'X-Project-Domain-Id',
            'X-Project-Domain-Name',
            'X-User-Id',
            'X-User-Name',
            'X-User-Domain-Id',
            'X-User-Domain-Name',
            'X-Roles',
            'X-Service-Catalog',
            # Deprecated
            'X-User',
            'X-Tenant-Id',
            'X-Tenant-Name',
            'X-Tenant',
            'X-Role',
        )
        self.LOG.debug('Removing headers from request environment: %s' %
                       ','.join(auth_headers))
        self._remove_headers(env, auth_headers)

    def _get_user_token_from_header(self, env):
        """Get token id from request.

        :param env: wsgi request environment
        :return token id
        :raises InvalidUserToken if no token is provided in request

        """
        token = self._get_header(env, 'X-Auth-Token',
                                 self._get_header(env, 'X-Storage-Token'))
        if token:
            return token
        else:
            if not self.delay_auth_decision:
                self.LOG.warn("Unable to find authentication token"
                              " in headers")
                self.LOG.debug("Headers: %s", env)
            raise InvalidUserToken('Unable to find token in headers')

    def _reject_request(self, env, start_response):
        """Redirect client to auth server.

        :param env: wsgi request environment
        :param start_response: wsgi response callback
        :returns HTTPUnauthorized http response

        """
        headers = [('WWW-Authenticate', 'Keystone uri=\'%s\'' % self.auth_uri)]
        resp = MiniResp('Authentication required', env, headers)
        start_response('401 Unauthorized', resp.headers)
        return resp.body

    def get_admin_token(self):
        """Return admin token, possibly fetching a new one.

        if self.admin_token_expiry is set from fetching an admin token, check
        it for expiration, and request a new token is the existing token
        is about to expire.

        :return admin token id
        :raise ServiceError when unable to retrieve token from keystone

        """
        if self.admin_token_expiry:
            if will_expire_soon(self.admin_token_expiry):
                self.admin_token = None

        if not self.admin_token:
            (self.admin_token,
             self.admin_token_expiry) = self._request_admin_token()

        return self.admin_token

    def _get_http_connection(self):
        if self.auth_protocol == 'http':
            return self.http_client_class(self.auth_host, self.auth_port,
                                          timeout=self.http_connect_timeout)
        else:
            return self.http_client_class(self.auth_host,
                                          self.auth_port,
                                          self.key_file,
                                          self.cert_file,
                                          timeout=self.http_connect_timeout)

    def _http_request(self, method, path, **kwargs):
        """HTTP request helper used to make unspecified content type requests.

        :param method: http method
        :param path: relative request url
        :return (http response object, response body)
        :raise ServerError when unable to communicate with keystone

        """
        conn = self._get_http_connection()

        RETRIES = self.http_request_max_retries
        retry = 0
        while True:
            try:
                conn.request(method, path, **kwargs)
                response = conn.getresponse()
                body = response.read()
                break
            except Exception as e:
                if retry == RETRIES:
                    self.LOG.error('HTTP connection exception: %s' % e)
                    raise NetworkError('Unable to communicate with keystone')
                # NOTE(vish): sleep 0.5, 1, 2
                self.LOG.warn('Retrying on HTTP connection exception: %s' % e)
                time.sleep(2.0 ** retry / 2)
                retry += 1
            finally:
                conn.close()

        return response, body

    def _json_request(self, method, path, body=None, additional_headers=None):
        """HTTP request helper used to make json requests.

        :param method: http method
        :param path: relative request url
        :param body: dict to encode to json as request body. Optional.
        :param additional_headers: dict of additional headers to send with
                                   http request. Optional.
        :return (http response object, response body parsed as json)
        :raise ServerError when unable to communicate with keystone

        """
        kwargs = {
            'headers': {
                'Content-type': 'application/json',
                'Accept': 'application/json',
            },
        }

        if additional_headers:
            kwargs['headers'].update(additional_headers)

        if body:
            kwargs['body'] = jsonutils.dumps(body)

        path = self.auth_admin_prefix + path

        response, body = self._http_request(method, path, **kwargs)

        try:
            data = jsonutils.loads(body)
        except ValueError:
            self.LOG.debug('Keystone did not return json-encoded body')
            data = {}

        return response, data

    def _request_admin_token(self):
        """Retrieve new token as admin user from keystone.

        :return token id upon success
        :raises ServerError when unable to communicate with keystone

        Irrespective of the auth version we are going to use for the
        user token, for simplicity we always use a v2 admin token to
        validate the user token.

        """
        params = {
            'auth': {
                'passwordCredentials': {
                    'username': self.admin_user,
                    'password': self.admin_password,
                },
                'tenantName': self.admin_tenant_name,
            }
        }

        response, data = self._json_request('POST',
                                            '/v2.0/tokens',
                                            body=params)

        try:
            token = data['access']['token']['id']
            expiry = data['access']['token']['expires']
            if not (token and expiry):
                raise AssertionError('invalid token or expire')
            datetime_expiry = timeutils.parse_isotime(expiry)
            return (token, timeutils.normalize_time(datetime_expiry))
        except (AssertionError, KeyError):
            self.LOG.warn(
                "Unexpected response from keystone service: %s", data)
            raise ServiceError('invalid json response')
        except (ValueError):
            self.LOG.warn(
                "Unable to parse expiration time from token: %s", data)
            raise ServiceError('invalid json response')

    def _validate_user_token(self, user_token, retry=True):
        """Authenticate user using PKI

        :param user_token: user's token id
        :param retry: Ignored, as it is not longer relevant
        :return uncrypted body of the token if the token is valid
        :raise InvalidUserToken if token is rejected
        :no longer raises ServiceError since it no longer makes RPC

        """
        try:
            token_id = cms.cms_hash_token(user_token)
            cached = self._cache_get(token_id)
            if cached:
                return cached
            if cms.is_ans1_token(user_token):
                verified = self.verify_signed_token(user_token)
                data = json.loads(verified)
            else:
                data = self.verify_uuid_token(user_token, retry)
            expires = self._confirm_token_not_expired(data)
            self._cache_put(token_id, data, expires)
            return data
        except NetworkError as e:
            self.LOG.debug('Token validation failure.', exc_info=True)
            self.LOG.warn("Authorization failed for token %s", user_token)
            raise InvalidUserToken('Token authorization failed')
        except Exception as e:
            self.LOG.debug('Token validation failure.', exc_info=True)
            self._cache_store_invalid(user_token)
            self.LOG.warn("Authorization failed for token %s", user_token)
            raise InvalidUserToken('Token authorization failed')

    def _token_is_v2(self, token_info):
        return ('access' in token_info)

    def _token_is_v3(self, token_info):
        return ('token' in token_info)

    def _build_user_headers(self, token_info):
        """Convert token object into headers.

        Build headers that represent authenticated user - see main
        doc info at start of file for details of headers to be defined.

        :param token_info: token object returned by keystone on authentication
        :raise InvalidUserToken when unable to parse token object

        """
        def get_tenant_info():
            """Returns a (tenant_id, tenant_name) tuple from context."""
            def essex():
                """Essex puts the tenant ID and name on the token."""
                return (token['tenant']['id'], token['tenant']['name'])

            def pre_diablo():
                """Pre-diablo, Keystone only provided tenantId."""
                return (token['tenantId'], token['tenantId'])

            def default_tenant():
                """Pre-grizzly, assume the user's default tenant."""
                return (user['tenantId'], user['tenantName'])

            for method in [essex, pre_diablo, default_tenant]:
                try:
                    return method()
                except KeyError:
                    pass

            raise InvalidUserToken('Unable to determine tenancy.')

        # For clarity. set all those attributes that are optional in
        # either a v2 or v3 token to None first
        domain_id = None
        domain_name = None
        project_id = None
        project_name = None
        user_domain_id = None
        user_domain_name = None
        project_domain_id = None
        project_domain_name = None

        if self._token_is_v2(token_info):
            user = token_info['access']['user']
            token = token_info['access']['token']
            roles = ','.join([role['name'] for role in user.get('roles', [])])
            catalog_root = token_info['access']
            catalog_key = 'serviceCatalog'
            project_id, project_name = get_tenant_info()
        else:
            #v3 token
            token = token_info['token']
            user = token['user']
            user_domain_id = user['domain']['id']
            user_domain_name = user['domain']['name']
            roles = (','.join([role['name']
                     for role in token.get('roles', [])]))
            catalog_root = token
            catalog_key = 'catalog'
            # For v3, the server will put in the default project if there is
            # one, so no need for us to add it here (like we do for a v2 token)
            if 'domain' in token:
                domain_id = token['domain']['id']
                domain_name = token['domain']['name']
            elif 'project' in token:
                project_id = token['project']['id']
                project_name = token['project']['name']
                project_domain_id = token['project']['domain']['id']
                project_domain_name = token['project']['domain']['name']

        user_id = user['id']
        user_name = user['name']

        rval = {
            'X-Identity-Status': 'Confirmed',
            'X-Domain-Id': domain_id,
            'X-Domain-Name': domain_name,
            'X-Project-Id': project_id,
            'X-Project-Name': project_name,
            'X-Project-Domain-Id': project_domain_id,
            'X-Project-Domain-Name': project_domain_name,
            'X-User-Id': user_id,
            'X-User-Name': user_name,
            'X-User-Domain-Id': user_domain_id,
            'X-User-Domain-Name': user_domain_name,
            'X-Roles': roles,
            # Deprecated
            'X-User': user_name,
            'X-Tenant-Id': project_id,
            'X-Tenant-Name': project_name,
            'X-Tenant': project_name,
            'X-Role': roles,
        }

        try:
            catalog = catalog_root[catalog_key]
            rval['X-Service-Catalog'] = jsonutils.dumps(catalog)
        except KeyError:
            pass

        return rval

    def _header_to_env_var(self, key):
        """Convert header to wsgi env variable.

        :param key: http header name (ex. 'X-Auth-Token')
        :return wsgi env variable name (ex. 'HTTP_X_AUTH_TOKEN')

        """
        return 'HTTP_%s' % key.replace('-', '_').upper()

    def _add_headers(self, env, headers):
        """Add http headers to environment."""
        for (k, v) in six.iteritems(headers):
            env_key = self._header_to_env_var(k)
            env[env_key] = v

    def _remove_headers(self, env, keys):
        """Remove http headers from environment."""
        for k in keys:
            env_key = self._header_to_env_var(k)
            try:
                del env[env_key]
            except KeyError:
                pass

    def _get_header(self, env, key, default=None):
        """Get http header from environment."""
        env_key = self._header_to_env_var(key)
        return env.get(env_key, default)

    def _cache_get(self, token, ignore_expires=False):
        """Return token information from cache.

        If token is invalid raise InvalidUserToken
        return token only if fresh (not expired).
        """

        if self._cache and token:
            if self._memcache_security_strategy is None:
                key = CACHE_KEY_TEMPLATE % token
                serialized = self._cache.get(key)
            else:
                keys = memcache_crypt.derive_keys(
                    token,
                    self._memcache_secret_key,
                    self._memcache_security_strategy)
                cache_key = CACHE_KEY_TEMPLATE % (
                    memcache_crypt.get_cache_key(keys))
                raw_cached = self._cache.get(cache_key)
                try:
                    # unprotect_data will return None if raw_cached is None
                    serialized = memcache_crypt.unprotect_data(keys,
                                                               raw_cached)
                except Exception:
                    msg = 'Failed to decrypt/verify cache data'
                    self.LOG.exception(msg)
                    # this should have the same effect as data not
                    # found in cache
                    serialized = None

            if serialized is None:
                return None

            # Note that 'invalid' and (data, expires) are the only
            # valid types of serialized cache entries, so there is not
            # a collision with json.loads(serialized) == None.
            cached = json.loads(serialized)
            if cached == 'invalid':
                self.LOG.debug('Cached Token %s is marked unauthorized', token)
                raise InvalidUserToken('Token authorization failed')

            data, expires = cached
            if ignore_expires or time.time() < float(expires):
                self.LOG.debug('Returning cached token %s', token)
                return data
            else:
                self.LOG.debug('Cached Token %s seems expired', token)

    def _cache_store(self, token, data):
        """Store value into memcache.

        data may be the string 'invalid' or a tuple like (data, expires)

        """
        serialized_data = json.dumps(data)
        if self._memcache_security_strategy is None:
            cache_key = CACHE_KEY_TEMPLATE % token
            data_to_store = serialized_data
        else:
            keys = memcache_crypt.derive_keys(
                token,
                self._memcache_secret_key,
                self._memcache_security_strategy)
            cache_key = CACHE_KEY_TEMPLATE % memcache_crypt.get_cache_key(keys)
            data_to_store = memcache_crypt.protect_data(keys, serialized_data)

        # Historically the swift cache conection used the argument
        # timeout= for the cache timeout, but this has been unified
        # with the official python memcache client with time= since
        # grizzly, we still need to handle folsom for a while until
        # this could get removed.
        try:
            self._cache.set(cache_key,
                            data_to_store,
                            time=self.token_cache_time)
        except(TypeError):
            self._cache.set(cache_key,
                            data_to_store,
                            timeout=self.token_cache_time)

    def _confirm_token_not_expired(self, data):
        if not data:
            raise InvalidUserToken('Token authorization failed')
        if self._token_is_v2(data):
            timestamp = data['access']['token']['expires']
        elif self._token_is_v3(data):
            timestamp = data['token']['expires_at']
        else:
            raise InvalidUserToken('Token authorization failed')
        expires = timeutils.parse_isotime(timestamp).strftime('%s')
        if time.time() >= float(expires):
            self.LOG.debug('Token expired a %s', timestamp)
            raise InvalidUserToken('Token authorization failed')
        return expires

    def _cache_put(self, token, data, expires):
        """Put token data into the cache.

        Stores the parsed expire date in cache allowing
        quick check of token freshness on retrieval.

        """
        if self._cache:
                self.LOG.debug('Storing %s token in memcache', token)
                self._cache_store(token, (data, expires))

    def _cache_store_invalid(self, token):
        """Store invalid token in cache."""
        if self._cache:
            self.LOG.debug(
                'Marking token %s as unauthorized in memcache', token)
            self._cache_store(token, 'invalid')

    def cert_file_missing(self, proc_output, file_name):
        return (file_name in proc_output and not os.path.exists(file_name))

    def verify_uuid_token(self, user_token, retry=True):
        """Authenticate user token with keystone.

        :param user_token: user's token id
        :param retry: flag that forces the middleware to retry
                      user authentication when an indeterminate
                      response is received. Optional.
        :return token object received from keystone on success
        :raise InvalidUserToken if token is rejected
        :raise ServiceError if unable to authenticate token

        """
        # Determine the highest api version we can use.
        if not self.auth_version:
            self.auth_version = self._choose_api_version()

        if self.auth_version == 'v3.0':
            headers = {'X-Auth-Token': self.get_admin_token(),
                       'X-Subject-Token': safe_quote(user_token)}
            response, data = self._json_request(
                'GET',
                '/v3/auth/tokens',
                additional_headers=headers)
        else:
            headers = {'X-Auth-Token': self.get_admin_token()}
            response, data = self._json_request(
                'GET',
                '/v2.0/tokens/%s' % safe_quote(user_token),
                additional_headers=headers)

        if response.status == 200:
            return data
        if response.status == 404:
            self.LOG.warn("Authorization failed for token %s", user_token)
            raise InvalidUserToken('Token authorization failed')
        if response.status == 401:
            self.LOG.info(
                'Keystone rejected admin token %s, resetting', headers)
            self.admin_token = None
        else:
            self.LOG.error('Bad response code while validating token: %s' %
                           response.status)
        if retry:
            self.LOG.info('Retrying validation')
            return self._validate_user_token(user_token, False)
        else:
            self.LOG.warn("Invalid user token: %s. Keystone response: %s.",
                          user_token, data)

            raise InvalidUserToken()

    def is_signed_token_revoked(self, signed_text):
        """Indicate whether the token appears in the revocation list."""
        revocation_list = self.token_revocation_list
        revoked_tokens = revocation_list.get('revoked', [])
        if not revoked_tokens:
            return
        revoked_ids = (x['id'] for x in revoked_tokens)
        token_id = utils.hash_signed_token(signed_text)
        for revoked_id in revoked_ids:
            if token_id == revoked_id:
                self.LOG.debug('Token %s is marked as having been revoked',
                               token_id)
                return True
        return False

    def cms_verify(self, data):
        """Verifies the signature of the provided data's IAW CMS syntax.

        If either of the certificate files are missing, fetch them and
        retry.
        """
        while True:
            try:
                output = cms.cms_verify(data, self.signing_cert_file_name,
                                        self.ca_file_name)
            except cms.subprocess.CalledProcessError as err:
                if self.cert_file_missing(err.output,
                                          self.signing_cert_file_name):
                    self.fetch_signing_cert()
                    continue
                if self.cert_file_missing(err.output, self.ca_file_name):
                    self.fetch_ca_cert()
                    continue
                self.LOG.warning('Verify error: %s' % err)
                raise err
            return output

    def verify_signed_token(self, signed_text):
        """Check that the token is unrevoked and has a valid signature."""
        if self.is_signed_token_revoked(signed_text):
            raise InvalidUserToken('Token has been revoked')

        formatted = cms.token_to_cms(signed_text)
        return self.cms_verify(formatted)

    def verify_signing_dir(self):
        if os.path.exists(self.signing_dirname):
            if not os.access(self.signing_dirname, os.W_OK):
                raise ConfigurationError(
                    'unable to access signing_dir %s' % self.signing_dirname)
            if os.stat(self.signing_dirname).st_uid != os.getuid():
                self.LOG.warning(
                    'signing_dir is not owned by %s' % os.getuid())
            current_mode = stat.S_IMODE(os.stat(self.signing_dirname).st_mode)
            if current_mode != stat.S_IRWXU:
                self.LOG.warning(
                    'signing_dir mode is %s instead of %s' %
                    (oct(current_mode), oct(stat.S_IRWXU)))
        else:
            os.makedirs(self.signing_dirname, stat.S_IRWXU)

    @property
    def token_revocation_list_fetched_time(self):
        if not self._token_revocation_list_fetched_time:
            # If the fetched list has been written to disk, use its
            # modification time.
            if os.path.exists(self.revoked_file_name):
                mtime = os.path.getmtime(self.revoked_file_name)
                fetched_time = datetime.datetime.fromtimestamp(mtime)
            # Otherwise the list will need to be fetched.
            else:
                fetched_time = datetime.datetime.min
            self._token_revocation_list_fetched_time = fetched_time
        return self._token_revocation_list_fetched_time

    @token_revocation_list_fetched_time.setter
    def token_revocation_list_fetched_time(self, value):
        self._token_revocation_list_fetched_time = value

    @property
    def token_revocation_list(self):
        timeout = (self.token_revocation_list_fetched_time +
                   self.token_revocation_list_cache_timeout)
        list_is_current = timeutils.utcnow() < timeout

        if list_is_current:
            # Load the list from disk if required
            if not self._token_revocation_list:
                with open(self.revoked_file_name, 'r') as f:
                    self._token_revocation_list = jsonutils.loads(f.read())
        else:
            self.token_revocation_list = self.fetch_revocation_list()
        return self._token_revocation_list

    @token_revocation_list.setter
    def token_revocation_list(self, value):
        """Save a revocation list to memory and to disk.

        :param value: A json-encoded revocation list

        """
        self._token_revocation_list = jsonutils.loads(value)
        self.token_revocation_list_fetched_time = timeutils.utcnow()
        with open(self.revoked_file_name, 'w') as f:
            f.write(value)

    def fetch_revocation_list(self, retry=True):
        headers = {'X-Auth-Token': self.get_admin_token()}
        response, data = self._json_request('GET', '/v2.0/tokens/revoked',
                                            additional_headers=headers)
        if response.status == 401:
            if retry:
                self.LOG.info(
                    'Keystone rejected admin token %s, resetting admin token',
                    headers)
                self.admin_token = None
                return self.fetch_revocation_list(retry=False)
        if response.status != 200:
            raise ServiceError('Unable to fetch token revocation list.')
        if 'signed' not in data:
            raise ServiceError('Revocation list improperly formatted.')
        return self.cms_verify(data['signed'])

    def fetch_signing_cert(self):
        path = self.auth_admin_prefix.rstrip('/')
        path += '/v2.0/certificates/signing'
        response, data = self._http_request('GET', path)

        def write_cert_file(data):
            certfile = open(self.signing_cert_file_name, 'w')
            certfile.write(data)
            certfile.close()

        try:
            #todo check response
            try:
                write_cert_file(data)
            except IOError:
                self.verify_signing_dir()
                write_cert_file(data)
        except (AssertionError, KeyError):
            self.LOG.warn(
                "Unexpected response from keystone service: %s", data)
            raise ServiceError('invalid json response')

    def fetch_ca_cert(self):
        path = self.auth_admin_prefix.rstrip('/') + '/v2.0/certificates/ca'
        response, data = self._http_request('GET', path)

        try:
            #todo check response
            certfile = open(self.ca_file_name, 'w')
            certfile.write(data)
            certfile.close()
        except (AssertionError, KeyError):
            self.LOG.warn(
                "Unexpected response from keystone service: %s", data)
            raise ServiceError('invalid json response')


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    conf = global_conf.copy()
    conf.update(local_conf)

    def auth_filter(app):
        return AuthProtocol(app, conf)
    return auth_filter


def app_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)
    return AuthProtocol(None, conf)
