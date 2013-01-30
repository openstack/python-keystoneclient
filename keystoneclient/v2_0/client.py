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
import logging

from keystoneclient import access
from keystoneclient import client
from keystoneclient import exceptions
from keystoneclient import service_catalog
from keystoneclient.v2_0 import ec2
from keystoneclient.v2_0 import endpoints
from keystoneclient.v2_0 import roles
from keystoneclient.v2_0 import services
from keystoneclient.v2_0 import tenants
from keystoneclient.v2_0 import tokens
from keystoneclient.v2_0 import users


_logger = logging.getLogger(__name__)


class Client(client.HTTPClient):
    """Client for the OpenStack Keystone v2.0 API.

    :param string username: Username for authentication. (optional)
    :param string password: Password for authentication. (optional)
    :param string token: Token for authentication. (optional)
    :param string tenant_id: Tenant id. (optional)
    :param string tenant_name: Tenant name. (optional)
    :param string auth_url: Keystone service endpoint for authorization.
    :param string region_name: Name of a region to select when choosing an
                               endpoint from the service catalog.
    :param string endpoint: A user-supplied endpoint URL for the keystone
                            service.  Lazy-authentication is possible for API
                            service calls if endpoint is set at
                            instantiation.(optional)
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    :param string original_ip: The original IP of the requesting user
                               which will be sent to Keystone in a
                               'Forwarded' header. (optional)
    :param string cert: If provided, used as a local certificate to communicate
                        with the keystone endpoint. If provided, requires the
                        additional parameter key. (optional)
    :param string key: The key associated with the certificate for secure
                       keystone communication. (optional)
    :param string cacert: the ca-certs to verify the secure communications
                          with keystone. (optional)
    :param boolean insecure: If using an SSL endpoint, allows for the certicate
                             to be unsigned - does not verify the certificate
                             chain. default: False (optional)
    :param dict auth_ref: To allow for consumers of the client to manage their
                          own caching strategy, you may initialize a client
                          with a previously captured auth_reference (token)
    :param boolean debug: Enables debug logging of all request and responses
                          to keystone. default False (option)

    .. warning::

    If debug is enabled, it may show passwords in plain text as a part of its
    output.


    The client can be created and used like a user or in a strictly
    bootstrap mode. Normal operation expects a username, password, auth_url,
    and tenant_name or id to be provided. Other values will be lazily loaded
    as needed from the service catalog.

    Example::

        >>> from keystoneclient.v2_0 import client
        >>> keystone = client.Client(username=USER,
                                     password=PASS,
                                     tenant_name=TENANT_NAME,
                                     auth_url=KEYSTONE_URL)
        >>> keystone.tenants.list()
        ...
        >>> user = keystone.users.get(USER_ID)
        >>> user.delete()

    Once authenticated, you can store and attempt to re-use the
    authenticated token. the auth_ref property on the client
    returns as a dictionary-like-object so that you can export and
    cache it, re-using it when initiating another client::

        >>> from keystoneclient.v2_0 import client
        >>> keystone = client.Client(username=USER,
                                     password=PASS,
                                     tenant_name=TENANT_NAME,
                                     auth_url=KEYSTONE_URL)
        >>> auth_ref = keystone.auth_ref
        >>> # pickle or whatever you like here
        >>> new_client = client.Client(auth_ref=auth_ref)

    Alternatively, you can provide the administrative token configured in
    keystone and an endpoint to communicate with directly. See
    (``admin_token`` in ``keystone.conf``) In this case, authenticate()
    is not needed, and no service catalog will be loaded.

    Example::

        >>> from keystoneclient.v2_0 import client
        >>> admin_client = client.Client(
                token='12345secret7890',
                endpoint='http://localhost:35357/v2.0')
        >>> keystone.tenants.list()

    """

    def __init__(self, **kwargs):
        """ Initialize a new client for the Keystone v2.0 API. """
        super(Client, self).__init__(**kwargs)
        self.endpoints = endpoints.EndpointManager(self)
        self.roles = roles.RoleManager(self)
        self.services = services.ServiceManager(self)
        self.tenants = tenants.TenantManager(self)
        self.tokens = tokens.TokenManager(self)
        self.users = users.UserManager(self)

        # extensions
        self.ec2 = ec2.CredentialsManager(self)

        if self.management_url is None:
            self.authenticate()

    #TODO(heckj): move to a method on auth_ref
    def has_service_catalog(self):
        """Returns True if this client provides a service catalog."""
        return hasattr(self, 'service_catalog')

    def process_token(self):
        """ Extract and process information from the new auth_ref.

        And set the relevant authentication information.
        """
        # if we got a response without a service catalog, set the local
        # list of tenants for introspection, and leave to client user
        # to determine what to do. Otherwise, load up the service catalog
        self.auth_token = self.auth_ref.auth_token
        if self.auth_ref.scoped:
            if self.management_url is None and self.auth_ref.management_url:
                self.management_url = self.auth_ref.management_url[0]
            self.tenant_name = self.auth_ref.tenant_name
            self.tenant_id = self.auth_ref.tenant_id
            self.user_id = self.auth_ref.user_id
        self._extract_service_catalog(self.auth_url, self.auth_ref)

    def get_raw_token_from_identity_service(self, auth_url, username=None,
                                            password=None, tenant_name=None,
                                            tenant_id=None, token=None):
        """ Authenticate against the Keystone API.

        :returns: ``raw token`` if authentication was successful.
        :raises: AuthorizationFailure if unable to authenticate or validate
                 the existing authorization token
        :raises: ValueError if insufficient parameters are used.

        """
        try:
            return self._base_authN(auth_url,
                                    username=username,
                                    tenant_id=tenant_id,
                                    tenant_name=tenant_name,
                                    password=password,
                                    token=token)
        except (exceptions.AuthorizationFailure, exceptions.Unauthorized):
            _logger.debug("Authorization Failed.")
            raise
        except Exception as e:
            raise exceptions.AuthorizationFailure("Authorization Failed: "
                                                  "%s" % e)

    def _base_authN(self, auth_url, username=None, password=None,
                    tenant_name=None, tenant_id=None, token=None):
        """ Takes a username, password, and optionally a tenant_id or
        tenant_name to get an authentication token from keystone.
        May also take a token and a tenant_id to re-scope a token
        to a tenant."""
        headers = {}
        url = auth_url + "/tokens"
        if token:
            headers['X-Auth-Token'] = token
            params = {"auth": {"token": {"id": token}}}
        elif username and password:
            params = {"auth": {"passwordCredentials": {"username": username,
                                                       "password": password}}}
        else:
            raise ValueError('A username and password or token is required.')
        if tenant_id:
            params['auth']['tenantId'] = tenant_id
        elif tenant_name:
            params['auth']['tenantName'] = tenant_name
        resp, body = self.request(url, 'POST', body=params, headers=headers)
        return body['access']

    # TODO(heckj): remove entirely in favor of access.AccessInfo and
    # associated methods
    def _extract_service_catalog(self, url, body):
        """ Set the client's service catalog from the response data. """
        self.service_catalog = service_catalog.ServiceCatalog(
            body, region_name=self.region_name)
        try:
            sc = self.service_catalog.get_token()
            # Save these since we have them and they'll be useful later
            self.auth_tenant_id = sc.get('tenant_id')
            self.auth_user_id = sc.get('user_id')
        except KeyError:
            raise exceptions.AuthorizationFailure()
