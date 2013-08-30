# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
# Copyright 2011 Nebula, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import copy
import logging
import urlparse

import requests

try:
    import keyring
    import pickle
except ImportError:
    keyring = None
    pickle = None

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from keystoneclient import access
from keystoneclient import exceptions
from keystoneclient.openstack.common import jsonutils


_logger = logging.getLogger(__name__)


USER_AGENT = 'python-keystoneclient'


def request(url, method='GET', headers=None, original_ip=None, debug=False,
            logger=None, **kwargs):
    """Perform a http request with standard settings.

    A wrapper around requests.request that adds standard headers like
    User-Agent and provides optional debug logging of the request.

    Arguments that are not handled are passed through to the requests library.

    :param string url: The url to make the request of.
    :param string method: The http method to use. (eg. 'GET', 'POST')
    :param dict headers: Headers to be included in the request. (optional)
    :param string original_ip: Mark this request as forwarded for this ip.
                               (optional)
    :param bool debug: Enable debug logging. (Defaults to False)
    :param logging.Logger logger: A logger to output to. (optional)

    :raises exceptions.ClientException: For connection failure, or to indicate
                                        an error response code.

    :returns: The response to the request.
    """

    if not headers:
        headers = dict()

    if not logger:
        logger = _logger

    headers.setdefault('User-Agent', USER_AGENT)

    if original_ip:
        headers['Forwarded'] = "for=%s;by=%s" % (original_ip, USER_AGENT)

    if debug:
        string_parts = ['curl -i']

        if method:
            string_parts.append(' -X %s' % method)

        string_parts.append(' %s' % url)

        if headers:
            for header in headers.iteritems():
                string_parts.append(' -H "%s: %s"' % header)

        logger.debug("REQ: %s" % "".join(string_parts))

        data = kwargs.get('data')
        if data:
            logger.debug("REQ BODY: %s\n" % data)

    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            **kwargs)
    except requests.ConnectionError:
        msg = 'Unable to establish connection to %s' % url
        raise exceptions.ClientException(msg)

    if debug:
        logger.debug("RESP: [%s] %s\nRESP BODY: %s\n",
                     resp.status_code, resp.headers, resp.text)

    if resp.status_code >= 400:
        logger.debug("Request returned failure status: %s",
                     resp.status_code)
        raise exceptions.from_response(resp, method, url)

    return resp


class HTTPClient(object):

    def __init__(self, username=None, tenant_id=None, tenant_name=None,
                 password=None, auth_url=None, region_name=None, timeout=None,
                 endpoint=None, token=None, cacert=None, key=None,
                 cert=None, insecure=False, original_ip=None, debug=False,
                 auth_ref=None, use_keyring=False, force_new_token=False,
                 stale_duration=None, user_id=None, user_domain_id=None,
                 user_domain_name=None, domain_id=None, domain_name=None,
                 project_id=None, project_name=None, project_domain_id=None,
                 project_domain_name=None, trust_id=None):
        """Construct a new http client

        :param string user_id: User ID for authentication. (optional)
        :param string username: Username for authentication. (optional)
        :param string user_domain_id: User's domain ID for authentication.
                                      (optional)
        :param string user_domain_name: User's domain name for authentication.
                                        (optional)
        :param string password: Password for authentication. (optional)
        :param string domain_id: Domain ID for domain scoping. (optional)
        :param string domain_name: Domain name for domain scoping. (optional)
        :param string project_id: Project ID for project scoping. (optional)
        :param string project_name: Project name for project scoping.
                                    (optional)
        :param string project_domain_id: Project's domain ID for project
                                         scoping. (optional)
        :param string project_domain_name: Project's domain name for project
                                           scoping. (optional)
        :param string auth_url: Identity service endpoint for authorization.
        :param string region_name: Name of a region to select when choosing an
                                   endpoint from the service catalog.
        :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
        :param string endpoint: A user-supplied endpoint URL for the identity
                                service.  Lazy-authentication is possible for
                                API service calls if endpoint is set at
                                instantiation. (optional)
        :param string token: Token for authentication. (optional)
        :param string cacert: Path to the Privacy Enhanced Mail (PEM) file
                              which contains the trusted authority X.509
                              certificates needed to established SSL connection
                              with the identity service. (optional)
        :param string key: Path to the Privacy Enhanced Mail (PEM) file which
                           contains the unencrypted client private key needed
                           to established two-way SSL connection with the
                           identity service. (optional)
        :param string cert: Path to the Privacy Enhanced Mail (PEM) file which
                            contains the corresponding X.509 client certificate
                            needed to established two-way SSL connection with
                            the identity service. (optional)
        :param boolean insecure: Does not perform X.509 certificate validation
                                 when establishing SSL connection with identity
                                 service. default: False (optional)
        :param string original_ip: The original IP of the requesting user
                                   which will be sent to identity service in a
                                   'Forwarded' header. (optional)
        :param boolean debug: Enables debug logging of all request and
                              responses to identity service.
                              default False (optional)
        :param dict auth_ref: To allow for consumers of the client to manage
                              their own caching strategy, you may initialize a
                              client with a previously captured auth_reference
                              (token). If there are keyword arguments passed
                              that also exist in auth_ref, the value from the
                              argument will take precedence.
        :param boolean use_keyring: Enables caching auth_ref into keyring.
                                    default: False (optional)
        :param boolean force_new_token: Keyring related parameter, forces
                                       request for new token.
                                       default: False (optional)
        :param integer stale_duration: Gap in seconds to determine if token
                                       from keyring is about to expire.
                                       default: 30 (optional)
        :param string tenant_name: Tenant name. (optional)
                                   The tenant_name keyword argument is
                                   deprecated, use project_name instead.
        :param string tenant_id: Tenant id. (optional)
                                 The tenant_id keyword argument is
                                 deprecated, use project_id instead.
        :param string trust_id: Trust ID for trust scoping. (optional)

        """
        # set baseline defaults

        self.user_id = None
        self.username = None
        self.user_domain_id = None
        self.user_domain_name = None

        self.domain_id = None
        self.domain_name = None

        self.project_id = None
        self.project_name = None
        self.project_domain_id = None
        self.project_domain_name = None

        self.auth_url = None
        self.management_url = None
        self.timeout = float(timeout) if timeout is not None else None

        self.trust_id = None

        # if loading from a dictionary passed in via auth_ref,
        # load values from AccessInfo parsing that dictionary
        if auth_ref:
            self.auth_ref = access.AccessInfo.factory(**auth_ref)
            self.version = self.auth_ref.version
            self.user_id = self.auth_ref.user_id
            self.username = self.auth_ref.username
            self.user_domain_id = self.auth_ref.user_domain_id
            self.domain_id = self.auth_ref.domain_id
            self.domain_name = self.auth_ref.domain_name
            self.project_id = self.auth_ref.project_id
            self.project_name = self.auth_ref.project_name
            self.project_domain_id = self.auth_ref.project_domain_id
            self.auth_url = self.auth_ref.auth_url[0]
            self.management_url = self.auth_ref.management_url[0]
            self.auth_token = self.auth_ref.auth_token
            self.trust_id = self.auth_ref.trust_id
        else:
            self.auth_ref = None

        # allow override of the auth_ref defaults from explicit
        # values provided to the client

        # apply deprecated variables first, so modern variables override them
        if tenant_id:
            self.project_id = tenant_id
        if tenant_name:
            self.project_name = tenant_name

        # user-related attributes
        self.password = password
        if user_id:
            self.user_id = user_id
        if username:
            self.username = username
        if user_domain_id:
            self.user_domain_id = user_domain_id
        elif not (user_id or user_domain_name):
            self.user_domain_id = 'default'
        if user_domain_name:
            self.user_domain_name = user_domain_name

        # domain-related attributes
        if domain_id:
            self.domain_id = domain_id
        if domain_name:
            self.domain_name = domain_name

        # project-related attributes
        if project_id:
            self.project_id = project_id
        if project_name:
            self.project_name = project_name
        if project_domain_id:
            self.project_domain_id = project_domain_id
        elif not (project_id or project_domain_name):
            self.project_domain_id = 'default'
        if project_domain_name:
            self.project_domain_name = project_domain_name

        # trust-related attributes
        if trust_id:
            self.trust_id = trust_id

        # endpoint selection
        if auth_url:
            self.auth_url = auth_url.rstrip('/')
        if token:
            self.auth_token_from_user = token
        else:
            self.auth_token_from_user = None
        if endpoint:
            self.management_url = endpoint.rstrip('/')
        self.region_name = region_name

        self.original_ip = original_ip
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
        if use_keyring and keyring is None:
            _logger.warning('Failed to load keyring modules.')
        self.use_keyring = use_keyring and keyring is not None
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

    @property
    def service_catalog(self):
        """Returns this client's service catalog."""
        return self.auth_ref.service_catalog

    def has_service_catalog(self):
        """Returns True if this client provides a service catalog."""
        return self.auth_ref.has_service_catalog()

    @property
    def tenant_id(self):
        """Provide read-only backwards compatibility for tenant_id.
           This is deprecated, use project_id instead.
        """
        return self.project_id

    @property
    def tenant_name(self):
        """Provide read-only backwards compatibility for tenant_name.
           This is deprecated, use project_name instead.
        """
        return self.project_name

    def authenticate(self, username=None, password=None, tenant_name=None,
                     tenant_id=None, auth_url=None, token=None,
                     user_id=None, domain_name=None, domain_id=None,
                     project_name=None, project_id=None, user_domain_id=None,
                     user_domain_name=None, project_domain_id=None,
                     project_domain_name=None, trust_id=None):
        """Authenticate user.

        Uses the data provided at instantiation to authenticate against
        the Identity server. This may use either a username and password
        or token for authentication. If a tenant name or id was provided
        then the resulting authenticated client will be scoped to that
        tenant and contain a service catalog of available endpoints.

        With the v2.0 API, if a tenant name or ID is not provided, the
        authentication token returned will be 'unscoped' and limited in
        capabilities until a fully-scoped token is acquired.

        With the v3 API, if a domain name or id was provided then the resulting
        authenticated client will be scoped to that domain. If a project name
        or ID is not provided, and the authenticating user has a default
        project configured, the authentication token returned will be 'scoped'
        to the default project. Otherwise, the authentication token returned
        will be 'unscoped' and limited in capabilities until a fully-scoped
        token is acquired.

        With the v3 API, with the OS-TRUST extension enabled, the trust_id can
        be provided to allow project-specific role delegation between users

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
        user_id = user_id or self.user_id
        username = username or self.username
        password = password or self.password

        user_domain_id = user_domain_id or self.user_domain_id
        user_domain_name = user_domain_name or self.user_domain_name
        domain_id = domain_id or self.domain_id
        domain_name = domain_name or self.domain_name
        project_id = project_id or tenant_id or self.project_id
        project_name = project_name or tenant_name or self.project_name
        project_domain_id = project_domain_id or self.project_domain_id
        project_domain_name = project_domain_name or self.project_domain_name

        trust_id = trust_id or self.trust_id

        if not token:
            token = self.auth_token_from_user
            if (not token and self.auth_ref and not
                    self.auth_ref.will_expire_soon(self.stale_duration)):
                token = self.auth_ref.auth_token

        kwargs = {
            'auth_url': auth_url,
            'user_id': user_id,
            'username': username,
            'user_domain_id': user_domain_id,
            'user_domain_name': user_domain_name,
            'domain_id': domain_id,
            'domain_name': domain_name,
            'project_id': project_id,
            'project_name': project_name,
            'project_domain_id': project_domain_id,
            'project_domain_name': project_domain_name,
            'token': token,
            'trust_id': trust_id,
        }
        (keyring_key, auth_ref) = self.get_auth_ref_from_keyring(**kwargs)
        new_token_needed = False
        if auth_ref is None or self.force_new_token:
            new_token_needed = True
            kwargs['password'] = password
            resp, body = self.get_raw_token_from_identity_service(**kwargs)
            self.auth_ref = access.AccessInfo.factory(resp, body)
        else:
            self.auth_ref = auth_ref
        self.process_token()
        if new_token_needed:
            self.store_auth_ref_into_keyring(keyring_key)
        return True

    def _build_keyring_key(self, **kwargs):
        """Create a unique key for keyring.

        Used to store and retrieve auth_ref from keyring.

        Returns a slash-separated string of values ordered by key name.

        """
        return '/'.join([kwargs[k] or '?' for k in sorted(kwargs.keys())])

    def get_auth_ref_from_keyring(self, **kwargs):
        """Retrieve auth_ref from keyring.

        If auth_ref is found in keyring, (keyring_key, auth_ref) is returned.
        Otherwise, (keyring_key, None) is returned.

        :returns: (keyring_key, auth_ref) or (keyring_key, None)
        :returns: or (None, None) if use_keyring is not set in the object

        """
        keyring_key = None
        auth_ref = None
        if self.use_keyring:
            keyring_key = self._build_keyring_key(**kwargs)
            try:
                auth_ref = keyring.get_password("keystoneclient_auth",
                                                keyring_key)
                if auth_ref:
                    auth_ref = pickle.loads(auth_ref)
                    if auth_ref.will_expire_soon(self.stale_duration):
                        # token has expired, don't use it
                        auth_ref = None
            except Exception as e:
                auth_ref = None
                _logger.warning('Unable to retrieve token from keyring %s' % (
                    e))
        return (keyring_key, auth_ref)

    def store_auth_ref_into_keyring(self, keyring_key):
        """Store auth_ref into keyring.

        """
        if self.use_keyring:
            try:
                keyring.set_password("keystoneclient_auth",
                                     keyring_key,
                                     pickle.dumps(self.auth_ref))
            except Exception as e:
                _logger.warning("Failed to store token into keyring %s" % (e))

    def process_token(self):
        """Extract and process information from the new auth_ref.

        And set the relevant authentication information.
        """
        # if we got a response without a service catalog, set the local
        # list of tenants for introspection, and leave to client user
        # to determine what to do. Otherwise, load up the service catalog
        if self.auth_ref.project_scoped:
            if not self.auth_ref.tenant_id:
                raise exceptions.AuthorizationFailure(
                    "Token didn't provide tenant_id")
            if self.management_url is None and self.auth_ref.management_url:
                self.management_url = self.auth_ref.management_url[0]
            self.project_name = self.auth_ref.tenant_name
            self.project_id = self.auth_ref.tenant_id

        if not self.auth_ref.user_id:
            raise exceptions.AuthorizationFailure(
                "Token didn't provide user_id")

        self.user_id = self.auth_ref.user_id

        self.auth_domain_id = self.auth_ref.domain_id
        self.auth_tenant_id = self.auth_ref.tenant_id
        self.auth_user_id = self.auth_ref.user_id

    def get_raw_token_from_identity_service(self, auth_url, username=None,
                                            password=None, tenant_name=None,
                                            tenant_id=None, token=None,
                                            user_id=None, user_domain_id=None,
                                            user_domain_name=None,
                                            domain_id=None, domain_name=None,
                                            project_id=None, project_name=None,
                                            project_domain_id=None,
                                            project_domain_name=None,
                                            trust_id=None):
        """Authenticate against the Identity API and get a token.

        Not implemented here because auth protocols should be API
        version-specific.

        Expected to authenticate or validate an existing authentication
        reference already associated with the client. Invoking this call
        *always* makes a call to the Identity service.

        :returns: (``resp``, ``body``)

        """
        raise NotImplementedError

    def _extract_service_catalog(self, url, body):
        """Set the client's service catalog from the response data.

        Not implemented here because data returned may be API
        version-specific.
        """
        raise NotImplementedError

    def serialize(self, entity):
        return jsonutils.dumps(entity)

    @property
    def service_catalog(self):
        """Returns this client's service catalog."""
        return self.auth_ref.service_catalog

    def has_service_catalog(self):
        """Returns True if this client provides a service catalog."""
        return self.auth_ref.has_service_catalog()

    def request(self, url, method, body=None, **kwargs):
        """Send an http request with the specified characteristics.

        Wrapper around requests.request to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.
        """
        # Copy the kwargs so we can reuse the original in case of redirects
        request_kwargs = copy.copy(kwargs)
        request_kwargs.setdefault('headers', kwargs.get('headers', {}))

        if body:
            request_kwargs['headers']['Content-Type'] = 'application/json'
            request_kwargs['data'] = self.serialize(body)

        if self.cert:
            request_kwargs.setdefault('cert', self.cert)
        if self.timeout is not None:
            request_kwargs.setdefault('timeout', self.timeout)

        resp = request(url, method, original_ip=self.original_ip,
                       verify=self.verify_cert, debug=self.debug_log,
                       **request_kwargs)

        if resp.text:
            try:
                body_resp = jsonutils.loads(resp.text)
            except (ValueError, TypeError):
                body_resp = None
                _logger.debug("Could not decode JSON from body: %s"
                              % resp.text)
        else:
            _logger.debug("No body was returned.")
            body_resp = None

        if resp.status_code in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self.request(resp.headers['location'], method, body,
                                **request_kwargs)

        return resp, body_resp

    def _cs_request(self, url, method, **kwargs):
        """Makes an authenticated request to keystone endpoint by
        concatenating self.management_url and url and passing in method and
        any associated kwargs.
        """

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
