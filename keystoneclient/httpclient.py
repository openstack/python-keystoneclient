# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack Foundation
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
"""OpenStack Client interface. Handles the REST calls and responses."""

import logging
import warnings

from debtcollector import removals
from debtcollector import renames
from keystoneauth1 import adapter
from oslo_serialization import jsonutils
import pkg_resources
from positional import positional
import requests

try:
    import pickle  # nosec(cjschaef): see bug 1534288 for details

    # NOTE(sdague): The conditional keyring import needs to only
    # trigger if it's a version of keyring that's supported in global
    # requirements. Update _min and _bad when that changes.
    keyring_v = pkg_resources.parse_version(
        pkg_resources.get_distribution("keyring").version)
    keyring_min = pkg_resources.parse_version('5.5.1')
    # This is a list of versions, e.g., pkg_resources.parse_version('3.3')
    keyring_bad = []

    if keyring_v >= keyring_min and keyring_v not in keyring_bad:
        import keyring
    else:
        keyring = None
except (ImportError, pkg_resources.DistributionNotFound):
    keyring = None
    pickle = None


from keystoneclient import _discover
from keystoneclient import access
from keystoneclient.auth import base
from keystoneclient import baseclient
from keystoneclient import exceptions
from keystoneclient.i18n import _
from keystoneclient import session as client_session


_logger = logging.getLogger(__name__)

USER_AGENT = client_session.USER_AGENT
"""Default user agent string.

This property is deprecated as of the 1.7.0 release in favor of
:data:`keystoneclient.session.USER_AGENT` and may be removed in the 2.0.0
release.
"""


@removals.remove(message='Use keystoneclient.session.request instead.',
                 version='1.7.0', removal_version='2.0.0')
def request(*args, **kwargs):
    """Make a request.

    This function is deprecated as of the 1.7.0 release in favor of
    :func:`keystoneclient.session.request` and may be removed in the
    2.0.0 release.
    """
    return client_session.request(*args, **kwargs)


class _FakeRequestSession(object):
    """This object is a temporary hack that should be removed later.

    Keystoneclient has a cyclical dependency with its managers which is
    preventing it from being cleaned up correctly. This is always bad but when
    we switched to doing connection pooling this object wasn't getting cleaned
    either and so we had left over TCP connections hanging around.

    Until we can fix the client cleanup we rollback the use of a requests
    session and do individual connections like we used to.
    """

    def request(self, *args, **kwargs):
        return requests.request(*args, **kwargs)


class _KeystoneAdapter(adapter.LegacyJsonAdapter):
    """A wrapper layer to interface keystoneclient with a session.

    An adapter provides a generic interface between a client and the session to
    provide client specific defaults. This object is passed to the managers.
    Keystoneclient managers have some additional requirements of variables that
    they expect to be present on the passed object.

    Subclass the existing adapter to provide those values that keystoneclient
    managers expect.
    """

    @property
    def user_id(self):
        """Best effort to retrieve the user_id from the plugin.

        Some managers rely on being able to get the currently authenticated
        user id. This is a problem when we are trying to abstract away the
        details of an auth plugin.

        For example changing a user's password can require access to the
        currently authenticated user_id.

        Perform a best attempt to fetch this data. It will work in the legacy
        case and with identity plugins and be None otherwise which is the same
        as the historical behavior.
        """
        # the identity plugin case
        try:
            return self.session.auth.get_access(self.session).user_id
        except AttributeError:  # nosec(cjschaef): attempt legacy retrival, or
            # return None
            pass

        # there is a case that we explicitly allow (tested by our unit tests)
        # that says you should be able to set the user_id on a legacy client
        # and it should overwrite the one retrieved via authentication. If it's
        # a legacy then self.session.auth is a client and we retrieve user_id.
        try:
            return self.session.auth.user_id
        except AttributeError:  # nosec(cjschaef): retrivals failed, return
            # None
            pass

        return None


class HTTPClient(baseclient.Client, base.BaseAuthPlugin):
    """HTTP client.

    .. warning::

        Creating an instance of this class without using the session argument
        is deprecated as of the 1.7.0 release and may be removed in the 2.0.0
        release.

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
    :param string project_name: Project name for project scoping. (optional)
    :param string project_domain_id: Project's domain ID for project scoping.
                                     (optional)
    :param string project_domain_name: Project's domain name for project
                                       scoping. (optional)
    :param string auth_url: Identity service endpoint for authorization.
    :param string region_name: Name of a region to select when choosing an
                               endpoint from the service catalog.
    :param integer timeout: This argument is deprecated as of the 1.7.0 release
                            in favor of session and may be removed in the 2.0.0
                            release. (optional)
    :param string endpoint: A user-supplied endpoint URL for the identity
                            service.  Lazy-authentication is possible for API
                            service calls if endpoint is set at instantiation.
                            (optional)
    :param string token: Token for authentication. (optional)
    :param string cacert: This argument is deprecated as of the 1.7.0 release
                          in favor of session and may be removed in the 2.0.0
                          release. (optional)
    :param string key: This argument is deprecated as of the 1.7.0 release
                       in favor of session and may be removed in the 2.0.0
                       release. (optional)
    :param string cert: This argument is deprecated as of the 1.7.0 release
                        in favor of session and may be removed in the 2.0.0
                        release. (optional)
    :param boolean insecure: This argument is deprecated as of the 1.7.0
                             release in favor of session and may be removed in
                             the 2.0.0 release. (optional)
    :param string original_ip: This argument is deprecated as of the 1.7.0
                               release in favor of session and may be removed
                               in the 2.0.0 release. (optional)
    :param dict auth_ref: To allow for consumers of the client to manage their
                          own caching strategy, you may initialize a client
                          with a previously captured auth_reference (token). If
                          there are keyword arguments passed that also exist in
                          auth_ref, the value from the argument will take
                          precedence.
    :param boolean use_keyring: Enables caching auth_ref into keyring.
                                default: False (optional)
    :param boolean force_new_token: Keyring related parameter, forces request
                                    for new token. default: False (optional)
    :param integer stale_duration: Gap in seconds to determine if token from
                                   keyring is about to expire. default: 30
                                   (optional)
    :param string tenant_name: Tenant name. (optional) The tenant_name keyword
                               argument is deprecated as of the 1.7.0 release
                               in favor of project_name and may be removed in
                               the 2.0.0 release.
    :param string tenant_id: Tenant id. (optional) The tenant_id keyword
                             argument is deprecated as of the 1.7.0 release in
                             favor of project_id and may be removed in the
                             2.0.0 release.
    :param string trust_id: Trust ID for trust scoping. (optional)
    :param object session: A Session object to be used for
                           communicating with the identity service.
    :type session: keystoneclient.session.Session
    :param string service_name: The default service_name for URL discovery.
                                default: None (optional)
    :param string interface: The default interface for URL discovery.
                             default: admin (optional)
    :param string endpoint_override: Always use this endpoint URL for requests
                                     for this client. (optional)
    :param auth: An auth plugin to use instead of the session one. (optional)
    :type auth: keystoneclient.auth.base.BaseAuthPlugin
    :param string user_agent: The User-Agent string to set.
                              default: python-keystoneclient (optional)
    :param int connect_retries: the maximum number of retries that should
                                be attempted for connection errors.
                                Default None - use session default which
                                is don't retry. (optional)
    """

    version = None

    @renames.renamed_kwarg('tenant_name', 'project_name', version='1.7.0',
                           removal_version='2.0.0')
    @renames.renamed_kwarg('tenant_id', 'project_id', version='1.7.0',
                           removal_version='2.0.0')
    @positional(enforcement=positional.WARN)
    def __init__(self, username=None, tenant_id=None, tenant_name=None,
                 password=None, auth_url=None, region_name=None, endpoint=None,
                 token=None, auth_ref=None, use_keyring=False,
                 force_new_token=False, stale_duration=None, user_id=None,
                 user_domain_id=None, user_domain_name=None, domain_id=None,
                 domain_name=None, project_id=None, project_name=None,
                 project_domain_id=None, project_domain_name=None,
                 trust_id=None, session=None, service_name=None,
                 interface='admin', endpoint_override=None, auth=None,
                 user_agent=USER_AGENT, connect_retries=None, **kwargs):
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
        self._endpoint = None
        self._management_url = None

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
            auth_urls = self.auth_ref.service_catalog.get_urls(
                service_type='identity', endpoint_type='public',
                region_name=region_name)
            self.auth_url = auth_urls[0]
            management_urls = self.auth_ref.service_catalog.get_urls(
                service_type='identity', endpoint_type='admin',
                region_name=region_name)
            self._management_url = management_urls[0]
            self.auth_token_from_user = self.auth_ref.auth_token
            self.trust_id = self.auth_ref.trust_id

            # TODO(blk-u): Using self.auth_ref.service_catalog._region_name is
            # deprecated and this code must be removed when the property is
            # actually removed.
            if self.auth_ref.has_service_catalog() and not region_name:
                region_name = self.auth_ref.service_catalog._region_name

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
            self._endpoint = endpoint.rstrip('/')
        self._auth_token = None

        if not session:

            warnings.warn(
                'Constructing an HTTPClient instance without using a session '
                'is deprecated as of the 1.7.0 release and may be removed in '
                'the 2.0.0 release.', DeprecationWarning)

            kwargs['session'] = _FakeRequestSession()
            session = client_session.Session._construct(kwargs)
            session.auth = self

        self.session = session
        self.domain = ''

        # NOTE(jamielennox): unfortunately we can't just use **kwargs here as
        # it would incompatibly limit the kwargs that can be passed to __init__
        # try and keep this list in sync with adapter.Adapter.__init__
        version = (
            _discover.normalize_version_number(self.version) if self.version
            else None)
        self._adapter = _KeystoneAdapter(session,
                                         service_type='identity',
                                         service_name=service_name,
                                         interface=interface,
                                         region_name=region_name,
                                         endpoint_override=endpoint_override,
                                         version=version,
                                         auth=auth,
                                         user_agent=user_agent,
                                         connect_retries=connect_retries)

        # keyring setup
        if use_keyring and keyring is None:
            _logger.warning('Failed to load keyring modules.')
        self.use_keyring = use_keyring and keyring is not None
        self.force_new_token = force_new_token
        self.stale_duration = stale_duration or access.STALE_TOKEN_DURATION
        self.stale_duration = int(self.stale_duration)

    def get_token(self, session, **kwargs):
        return self.auth_token

    @property
    def auth_token(self):
        if self._auth_token:
            return self._auth_token
        if self.auth_ref:
            if self.auth_ref.will_expire_soon(self.stale_duration):
                self.authenticate()
            return self.auth_ref.auth_token
        if self.auth_token_from_user:
            return self.auth_token_from_user

    def get_endpoint(self, session, interface=None, **kwargs):
        if interface == 'public' or interface is base.AUTH_INTERFACE:
            return self.auth_url
        else:
            return self.management_url

    def get_user_id(self, session, **kwargs):
        return self.auth_ref.user_id

    def get_project_id(self, session, **kwargs):
        return self.auth_ref.project_id

    @auth_token.setter
    def auth_token(self, value):
        """Override the auth_token.

        If an application sets auth_token explicitly then it will always be
        used and override any past or future retrieved token.
        """
        self._auth_token = value

    @auth_token.deleter
    def auth_token(self):
        self._auth_token = None
        self.auth_token_from_user = None

    @property
    def service_catalog(self):
        """Return this client's service catalog."""
        try:
            return self.auth_ref.service_catalog
        except AttributeError:
            return None

    def has_service_catalog(self):
        """Return True if this client provides a service catalog."""
        return self.auth_ref and self.auth_ref.has_service_catalog()

    @property
    def tenant_id(self):
        """Provide read-only backwards compatibility for tenant_id.

        .. warning::

            This is deprecated as of the 1.7.0 release in favor of project_id
            and may be removed in the 2.0.0 release.
        """
        warnings.warn(
            'tenant_id is deprecated as of the 1.7.0 release in favor of '
            'project_id and may be removed in the 2.0.0 release.',
            DeprecationWarning)

        return self.project_id

    @property
    def tenant_name(self):
        """Provide read-only backwards compatibility for tenant_name.

        .. warning::

            This is deprecated as of the 1.7.0 release in favor of project_name
            and may be removed in the 2.0.0 release.
        """
        warnings.warn(
            'tenant_name is deprecated as of the 1.7.0 release in favor of '
            'project_name and may be removed in the 2.0.0 release.',
            DeprecationWarning)

        return self.project_name

    @positional(enforcement=positional.WARN)
    def authenticate(self, username=None, password=None, tenant_name=None,
                     tenant_id=None, auth_url=None, token=None,
                     user_id=None, domain_name=None, domain_id=None,
                     project_name=None, project_id=None, user_domain_id=None,
                     user_domain_name=None, project_domain_id=None,
                     project_domain_name=None, trust_id=None,
                     region_name=None):
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
        :raises keystoneclient.exceptions.AuthorizationFailure: if unable to
            authenticate or validate the existing authorization token
        :raises keystoneclient.exceptions.ValueError: if insufficient
                                                      parameters are used.

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
        region_name = region_name or self._adapter.region_name

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
            resp = self.get_raw_token_from_identity_service(**kwargs)

            if isinstance(resp, access.AccessInfo):
                self.auth_ref = resp
            else:
                self.auth_ref = access.AccessInfo.factory(*resp)

            # NOTE(jamielennox): The original client relies on being able to
            # push the region name into the service catalog but new auth
            # it in.
            if region_name:
                self.auth_ref.service_catalog._region_name = region_name
        else:
            self.auth_ref = auth_ref

        self.process_token(region_name=region_name)
        if new_token_needed:
            self.store_auth_ref_into_keyring(keyring_key)
        return True

    def _build_keyring_key(self, **kwargs):
        """Create a unique key for keyring.

        Used to store and retrieve auth_ref from keyring.

        Return a slash-separated string of values ordered by key name.

        """
        return '/'.join([kwargs[k] or '?' for k in sorted(kwargs)])

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
                    auth_ref = pickle.loads(auth_ref)  # nosec(cjschaef): see
                    # bug 1534288
                    if auth_ref.will_expire_soon(self.stale_duration):
                        # token has expired, don't use it
                        auth_ref = None
            except Exception as e:
                auth_ref = None
                _logger.warning('Unable to retrieve token from keyring %s', e)
        return (keyring_key, auth_ref)

    def store_auth_ref_into_keyring(self, keyring_key):
        """Store auth_ref into keyring."""
        if self.use_keyring:
            try:
                keyring.set_password("keystoneclient_auth",
                                     keyring_key,
                                     pickle.dumps(self.auth_ref))  # nosec
                # (cjschaef): see bug 1534288
            except Exception as e:
                _logger.warning("Failed to store token into keyring %s", e)

    def _process_management_url(self, region_name):
        try:
            self._management_url = self.auth_ref.service_catalog.url_for(
                service_type='identity',
                endpoint_type='admin',
                region_name=region_name)
        except exceptions.EndpointNotFound as e:
            _logger.debug("Failed to find endpoint for management url %s", e)

    def process_token(self, region_name=None):
        """Extract and process information from the new auth_ref.

        And set the relevant authentication information.
        """
        # if we got a response without a service catalog, set the local
        # list of tenants for introspection, and leave to client user
        # to determine what to do. Otherwise, load up the service catalog
        if self.auth_ref.project_scoped:
            if not self.auth_ref.tenant_id:
                raise exceptions.AuthorizationFailure(
                    _("Token didn't provide tenant_id"))
            self._process_management_url(region_name)
            self.project_name = self.auth_ref.tenant_name
            self.project_id = self.auth_ref.tenant_id

        if not self.auth_ref.user_id:
            raise exceptions.AuthorizationFailure(
                _("Token didn't provide user_id"))

        self.user_id = self.auth_ref.user_id

        self.auth_domain_id = self.auth_ref.domain_id
        self.auth_tenant_id = self.auth_ref.tenant_id
        self.auth_user_id = self.auth_ref.user_id

    @property
    def management_url(self):
        return self._endpoint or self._management_url

    @management_url.setter
    def management_url(self, value):
        # NOTE(jamielennox): it's debatable here whether we should set
        # _endpoint or _management_url. As historically management_url was set
        # permanently setting _endpoint would better match that behaviour.
        self._endpoint = value

    @positional(enforcement=positional.WARN)
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

    def serialize(self, entity):
        return jsonutils.dumps(entity)

    @removals.remove(version='1.7.0', removal_version='2.0.0')
    def request(self, *args, **kwargs):
        """Send an http request with the specified characteristics.

        Wrapper around requests.request to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.

        .. warning::

            *DEPRECATED*: This function is no longer used. It was designed to
            be used only by the managers and the managers now receive an
            adapter so this function is no longer on the standard request path.
            This may be removed in the 2.0.0 release.
        """
        return self._request(*args, **kwargs)

    def _request(self, *args, **kwargs):
        kwargs.setdefault('authenticated', False)
        return self._adapter.request(*args, **kwargs)

    def _cs_request(self, url, method, management=True, **kwargs):
        """Make an authenticated request to keystone endpoint.

        Request are made to keystone endpoint by concatenating
        self.management_url and url and passing in method and
        any associated kwargs.
        """
        if not management:
            endpoint_filter = kwargs.setdefault('endpoint_filter', {})
            endpoint_filter.setdefault('interface', 'public')

        kwargs.setdefault('authenticated', None)
        return self._request(url, method, **kwargs)

    @removals.remove(version='1.7.0', removal_version='2.0.0')
    def get(self, url, **kwargs):
        """Perform an authenticated GET request.

        This calls :py:meth:`.request()` with ``method`` set to ``GET`` and an
        authentication token if one is available.

        .. warning::

            *DEPRECATED*: This function is no longer used and is deprecated as
            of the 1.7.0 release and may be removed in the 2.0.0 release. It
            was designed to be used by the managers and the managers now
            receive an adapter so this function is no longer on the standard
            request path.
        """
        return self._cs_request(url, 'GET', **kwargs)

    @removals.remove(version='1.7.0', removal_version='2.0.0')
    def head(self, url, **kwargs):
        """Perform an authenticated HEAD request.

        This calls :py:meth:`.request()` with ``method`` set to ``HEAD`` and an
        authentication token if one is available.

        .. warning::

            *DEPRECATED*: This function is no longer used and is deprecated as
            of the 1.7.0 release and may be removed in the 2.0.0 release. It
            was designed to be used by the managers and the managers now
            receive an adapter so this function is no longer on the standard
            request path.
        """
        return self._cs_request(url, 'HEAD', **kwargs)

    @removals.remove(version='1.7.0', removal_version='2.0.0')
    def post(self, url, **kwargs):
        """Perform an authenticate POST request.

        This calls :py:meth:`.request()` with ``method`` set to ``POST`` and an
        authentication token if one is available.

        .. warning::

            *DEPRECATED*: This function is no longer used and is deprecated as
            of the 1.7.0 release and may be removed in the 2.0.0 release. It
            was designed to be used by the managers and the managers now
            receive an adapter so this function is no longer on the standard
            request path.
        """
        return self._cs_request(url, 'POST', **kwargs)

    @removals.remove(version='1.7.0', removal_version='2.0.0')
    def put(self, url, **kwargs):
        """Perform an authenticate PUT request.

        This calls :py:meth:`.request()` with ``method`` set to ``PUT`` and an
        authentication token if one is available.

        .. warning::

            *DEPRECATED*: This function is no longer used and is deprecated as
            of the 1.7.0 release and may be removed in the 2.0.0 release. It
            was designed to be used by the managers and the managers now
            receive an adapter so this function is no longer on the standard
            request path.
        """
        return self._cs_request(url, 'PUT', **kwargs)

    @removals.remove(version='1.7.0', removal_version='2.0.0')
    def patch(self, url, **kwargs):
        """Perform an authenticate PATCH request.

        This calls :py:meth:`.request()` with ``method`` set to ``PATCH`` and
        an authentication token if one is available.

        .. warning::

            *DEPRECATED*: This function is no longer used and is deprecated as
            of the 1.7.0 release and may be removed in the 2.0.0 release. It
            was designed to be used by the managers and the managers now
            receive an adapter so this function is no longer on the standard
            request path.
        """
        return self._cs_request(url, 'PATCH', **kwargs)

    @removals.remove(version='1.7.0', removal_version='2.0.0')
    def delete(self, url, **kwargs):
        """Perform an authenticate DELETE request.

        This calls :py:meth:`.request()` with ``method`` set to ``DELETE`` and
        an authentication token if one is available.

        .. warning::

            *DEPRECATED*: This function is no longer used and is deprecated as
            of the 1.7.0 release and may be removed in the 2.0.0 release. It
            was designed to be used by the managers and the managers now
            receive an adapter so this function is no longer on the standard
            request path.
        """
        return self._cs_request(url, 'DELETE', **kwargs)

    deprecated_session_variables = {'original_ip': None,
                                    'cert': None,
                                    'timeout': None,
                                    'verify_cert': 'verify'}

    deprecated_adapter_variables = {'region_name': None}

    def __getattr__(self, name):
        """Fetch deprecated session variables."""
        try:
            var_name = self.deprecated_session_variables[name]
        except KeyError:  # nosec(cjschaef): try adapter variable or raise
            # an AttributeError
            pass
        else:
            warnings.warn(
                'The %s session variable is deprecated as of the 1.7.0 '
                'release and may be removed in the 2.0.0 release' % name,
                DeprecationWarning)
            return getattr(self.session, var_name or name)

        try:
            var_name = self.deprecated_adapter_variables[name]
        except KeyError:  # nosec(cjschaef): raise an AttributeError
            pass
        else:
            warnings.warn(
                'The %s adapter variable is deprecated as of the 1.7.0 '
                'release and may be removed in the 2.0.0 release' % name,
                DeprecationWarning)
            return getattr(self._adapter, var_name or name)

        raise AttributeError(_("Unknown Attribute: %s") % name)

    def __setattr__(self, name, val):
        """Assign value to deprecated seesion variables."""
        try:
            var_name = self.deprecated_session_variables[name]
        except KeyError:  # nosec(cjschaef): try adapter variable or call
            # parent class's __setattr__
            pass
        else:
            warnings.warn(
                'The %s session variable is deprecated as of the 1.7.0 '
                'release and may be removed in the 2.0.0 release' % name,
                DeprecationWarning)
            return setattr(self.session, var_name or name)

        try:
            var_name = self.deprecated_adapter_variables[name]
        except KeyError:  # nosec(cjschaef): call parent class's __setattr__
            pass
        else:
            warnings.warn(
                'The %s adapter variable is deprecated as of the 1.7.0 '
                'release and may be removed in the 2.0.0 release' % name,
                DeprecationWarning)
            return setattr(self._adapter, var_name or name)

        super(HTTPClient, self).__setattr__(name, val)
