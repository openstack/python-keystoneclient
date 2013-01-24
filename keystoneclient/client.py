# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
# Copyright 2011 Nebula, Inc.

# All Rights Reserved.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import copy
import logging
import sys
import urlparse

import requests

try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from keystoneclient import access
from keystoneclient import exceptions


_logger = logging.getLogger(__name__)


def try_import_keyring():
    try:
        import keyring  # noqa
        import pickle  # noqa
        return True
    except ImportError:
        if (hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()):
            print >> sys.stderr, 'Failed to load keyring modules.'
        else:
            _logger.warning('Failed to load keyring modules.')
        return False


class HTTPClient(object):

    USER_AGENT = 'python-keystoneclient'

    def __init__(self, username=None, tenant_id=None, tenant_name=None,
                 password=None, auth_url=None, region_name=None, timeout=None,
                 endpoint=None, token=None, cacert=None, key=None,
                 cert=None, insecure=False, original_ip=None, debug=False,
                 auth_ref=None, use_keyring=False, force_new_token=False,
                 stale_duration=None):
        """Construct a new http client

        @param: timeout the request libary timeout in seconds (default None)

        """
        self.version = 'v2.0'
        # set baseline defaults
        self.username = None
        self.tenant_id = None
        self.tenant_name = None
        self.auth_url = None
        self.management_url = None
        if timeout is not None:
            self.timeout = float(timeout)
        else:
            self.timeout = None
        # if loading from a dictionary passed in via auth_ref,
        # load values from AccessInfo parsing that dictionary
        self.auth_ref = access.AccessInfo(**auth_ref) if auth_ref else None
        if self.auth_ref:
            self.username = self.auth_ref.username
            self.tenant_id = self.auth_ref.tenant_id
            self.tenant_name = self.auth_ref.tenant_name
            self.auth_url = self.auth_ref.auth_url[0]
            self.management_url = self.auth_ref.management_url[0]
        # allow override of the auth_ref defaults from explicit
        # values provided to the client
        if username:
            self.username = username
        if tenant_id:
            self.tenant_id = tenant_id
        if tenant_name:
            self.tenant_name = tenant_name
        if auth_url:
            self.auth_url = auth_url.rstrip('/')
        if token:
            self.auth_token_from_user = token
        else:
            self.auth_token_from_user = None
        if endpoint:
            self.management_url = endpoint.rstrip('/')
        self.password = password
        self.original_ip = original_ip
        self.region_name = region_name
        if cacert:
            self.verify_cert = cacert
        else:
            self.verify_cert = True
        if insecure:
            self.verify_cert = False
        self.cert = cert
        if cert and key:
            self.cert = (cert, key,)
        self.domain = ''

        # logging setup
        self.debug_log = debug
        if self.debug_log and not _logger.handlers:
            ch = logging.StreamHandler()
            _logger.setLevel(logging.DEBUG)
            _logger.addHandler(ch)
            if hasattr(requests, 'logging'):
                requests.logging.getLogger(requests.__name__).addHandler(ch)

        # keyring setup
        self.use_keyring = use_keyring and try_import_keyring()
        self.force_new_token = force_new_token
        self.stale_duration = stale_duration or access.STALE_TOKEN_DURATION
        self.stale_duration = int(self.stale_duration)

    @property
    def auth_token(self):
        if self.auth_token_from_user:
            return self.auth_token_from_user
        if self.auth_ref:
            if self.auth_ref.will_expire_soon(self.stale_duration):
                self.authenticate()
            return self.auth_ref.auth_token

    @auth_token.setter
    def auth_token(self, value):
        self.auth_token_from_user = value

    @auth_token.deleter
    def auth_token(self):
        del self.auth_token_from_user

    def authenticate(self, username=None, password=None, tenant_name=None,
                     tenant_id=None, auth_url=None, token=None):
        """ Authenticate user.

        Uses the data provided at instantiation to authenticate against
        the Keystone server. This may use either a username and password
        or token for authentication. If a tenant name or id was provided
        then the resulting authenticated client will be scoped to that
        tenant and contain a service catalog of available endpoints.

        With the v2.0 API, if a tenant name or ID is not provided, the
        authenication token returned will be 'unscoped' and limited in
        capabilities until a fully-scoped token is acquired.

        If successful, sets the self.auth_ref and self.auth_token with
        the returned token. If not already set, will also set
        self.management_url from the details provided in the token.

        :returns: ``True`` if authentication was successful.
        :raises: AuthorizationFailure if unable to authenticate or validate
                 the existing authorization token
        :raises: ValueError if insufficient parameters are used.

        If keyring is used, token is retrieved from keyring instead.
        Authentication will only be necessary if any of the following
        conditions are met:

        * keyring is not used
        * if token is not found in keyring
        * if token retrieved from keyring is expired or about to
          expired (as determined by stale_duration)
        * if force_new_token is true

        """
        auth_url = auth_url or self.auth_url
        username = username or self.username
        password = password or self.password
        tenant_name = tenant_name or self.tenant_name
        tenant_id = tenant_id or self.tenant_id

        if not token:
            token = self.auth_token_from_user
            if (not token and self.auth_ref and not
                    self.auth_ref.will_expire_soon(self.stale_duration)):
                token = self.auth_ref.auth_token

        (keyring_key, auth_ref) = self.get_auth_ref_from_keyring(auth_url,
                                                                 username,
                                                                 tenant_name,
                                                                 tenant_id,
                                                                 token)
        new_token_needed = False
        if auth_ref is None or self.force_new_token:
            new_token_needed = True
            raw_token = self.get_raw_token_from_identity_service(auth_url,
                                                                 username,
                                                                 password,
                                                                 tenant_name,
                                                                 tenant_id,
                                                                 token)
            self.auth_ref = access.AccessInfo(**raw_token)
        else:
            self.auth_ref = auth_ref
        self.process_token()
        if new_token_needed:
            self.store_auth_ref_into_keyring(keyring_key)
        return True

    def _build_keyring_key(self, auth_url, username, tenant_name,
                           tenant_id, token):
        """ Create a unique key for keyring.

        Used to store and retrieve auth_ref from keyring.

        """
        keys = [auth_url, username, tenant_name, tenant_id, token]
        for index, key in enumerate(keys):
            if key is None:
                keys[index] = '?'
        keyring_key = '/'.join(keys)
        return keyring_key

    def get_auth_ref_from_keyring(self, auth_url, username, tenant_name,
                                  tenant_id, token):
        """ Retrieve auth_ref from keyring.

        If auth_ref is found in keyring, (keyring_key, auth_ref) is returned.
        Otherwise, (keyring_key, None) is returned.

        :returns: (keyring_key, auth_ref) or (keyring_key, None)

        """
        keyring_key = None
        auth_ref = None
        if self.use_keyring:
            keyring_key = self._build_keyring_key(auth_url, username,
                                                  tenant_name, tenant_id,
                                                  token)
            try:
                auth_ref = keyring.get_password("keystoneclient_auth",
                                                keyring_key)
                if auth_ref:
                    auth_ref = pickle.loads(auth_ref)
                    if self.auth_ref.will_expire_soon(self.stale_duration):
                        # token has expired, don't use it
                        auth_ref = None
            except Exception as e:
                auth_ref = None
                _logger.warning('Unable to retrieve token from keyring %s' % (
                    e))
        return (keyring_key, auth_ref)

    def store_auth_ref_into_keyring(self, keyring_key):
        """ Store auth_ref into keyring.

        """
        if self.use_keyring:
            try:
                keyring.set_password("keystoneclient_auth",
                                     keyring_key,
                                     pickle.dumps(self.auth_ref))
            except Exception as e:
                _logger.warning("Failed to store token into keyring %s" % (e))

    def process_token(self):
        """ Extract and process information from the new auth_ref.

        """
        raise NotImplementedError

    def get_raw_token_from_identity_service(self, auth_url, username=None,
                                            password=None, tenant_name=None,
                                            tenant_id=None, token=None):
        """ Authenticate against the Identity API and get a token.

        Not implemented here because auth protocols should be API
        version-specific.

        Expected to authenticate or validate an existing authentication
        reference already associated with the client. Invoking this call
        *always* makes a call to the Keystone.

        :returns: ``raw token``

        """
        raise NotImplementedError

    def _extract_service_catalog(self, url, body):
        """ Set the client's service catalog from the response data.

        Not implemented here because data returned may be API
        version-specific.
        """
        raise NotImplementedError

    def http_log_req(self, args, kwargs):
        if not self.debug_log:
            return

        string_parts = ['curl -i']
        for element in args:
            if element in ('GET', 'POST'):
                string_parts.append(' -X %s' % element)
            else:
                string_parts.append(' %s' % element)

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        _logger.debug("REQ: %s" % "".join(string_parts))
        if 'data' in kwargs:
            _logger.debug("REQ BODY: %s\n" % (kwargs['data']))

    def http_log_resp(self, resp):
        if self.debug_log:
            _logger.debug(
                "RESP: [%s] %s\nRESP BODY: %s\n",
                resp.status_code,
                resp.headers,
                resp.text)

    def serialize(self, entity):
        return json.dumps(entity)

    @property
    def service_catalog(self):
        """Returns this client's service catalog."""
        return self.auth_ref.service_catalog

    def has_service_catalog(self):
        """Returns True if this client provides a service catalog."""
        return self.auth_ref.has_service_catalog()

    def request(self, url, method, **kwargs):
        """ Send an http request with the specified characteristics.

        Wrapper around requests.request to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.
        """
        # Copy the kwargs so we can reuse the original in case of redirects
        request_kwargs = copy.copy(kwargs)
        request_kwargs.setdefault('headers', kwargs.get('headers', {}))
        request_kwargs['headers']['User-Agent'] = self.USER_AGENT
        if self.original_ip:
            request_kwargs['headers']['Forwarded'] = "for=%s;by=%s" % (
                self.original_ip, self.USER_AGENT)
        if 'body' in kwargs:
            request_kwargs['headers']['Content-Type'] = 'application/json'
            request_kwargs['data'] = self.serialize(kwargs['body'])
            del request_kwargs['body']
        if self.cert:
            request_kwargs['cert'] = self.cert
        if self.timeout is not None:
            request_kwargs.setdefault('timeout', self.timeout)

        self.http_log_req((url, method,), request_kwargs)

        try:
            resp = requests.request(
                method,
                url,
                verify=self.verify_cert,
                **request_kwargs)
        except requests.ConnectionError:
            msg = 'Unable to establish connection to %s' % url
            raise exceptions.ClientException(msg)

        self.http_log_resp(resp)

        if resp.text:
            try:
                body = json.loads(resp.text)
            except (ValueError, TypeError):
                body = None
                _logger.debug("Could not decode JSON from body: %s"
                              % resp.text)
        else:
            _logger.debug("No body was returned.")
            body = None

        if resp.status_code >= 400:
            _logger.debug(
                "Request returned failure status: %s",
                resp.status_code)
            raise exceptions.from_response(resp, body or resp.text)
        elif resp.status_code in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self.request(resp.headers['location'], method, **kwargs)

        return resp, body

    def _cs_request(self, url, method, **kwargs):
        """ Makes an authenticated request to keystone endpoint by
        concatenating self.management_url and url and passing in method and
        any associated kwargs. """

        is_management = kwargs.pop('management', True)

        if is_management and self.management_url is None:
            raise exceptions.AuthorizationFailure(
                'Current authorization does not have a known management url')

        url_to_use = self.auth_url
        if is_management:
            url_to_use = self.management_url

        kwargs.setdefault('headers', {})
        if self.auth_token:
            kwargs['headers']['X-Auth-Token'] = self.auth_token

        resp, body = self.request(url_to_use + url, method,
                                  **kwargs)
        return resp, body

    def get(self, url, **kwargs):
        return self._cs_request(url, 'GET', **kwargs)

    def head(self, url, **kwargs):
        return self._cs_request(url, 'HEAD', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def patch(self, url, **kwargs):
        return self._cs_request(url, 'PATCH', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)
