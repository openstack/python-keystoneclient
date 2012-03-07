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
    :param string tenant_name: Tenant id. (optional)
    :param string tenant_id: Tenant name. (optional)
    :param string auth_url: Keystone service endpoint for authorization.
    :param string region_name: Name of a region to select when choosing an
                               endpoint from the service catalog.
    :param string endpoint: A user-supplied endpoint URL for the keystone
                            service.  Lazy-authentication is possible for API
                            service calls if endpoint is set at
                            instantiation.(optional)
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)

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

    """

    def __init__(self, endpoint=None, **kwargs):
        """ Initialize a new client for the Keystone v2.0 API. """
        super(Client, self).__init__(endpoint=endpoint, **kwargs)
        self.endpoints = endpoints.EndpointManager(self)
        self.roles = roles.RoleManager(self)
        self.services = services.ServiceManager(self)
        self.tenants = tenants.TenantManager(self)
        self.tokens = tokens.TokenManager(self)
        self.users = users.UserManager(self)
        # NOTE(gabriel): If we have a pre-defined endpoint then we can
        #                get away with lazy auth. Otherwise auth immediately.

        # extensions
        self.ec2 = ec2.CredentialsManager(self)

        if endpoint is None:
            self.authenticate()
        else:
            self.management_url = endpoint

    def authenticate(self):
        """ Authenticate against the Keystone API.

        Uses the data provided at instantiation to authenticate against
        the Keystone server. This may use either a username and password
        or token for authentication. If a tenant id was provided
        then the resulting authenticated client will be scoped to that
        tenant and contain a service catalog of available endpoints.

        Returns ``True`` if authentication was successful.
        """
        self.management_url = self.auth_url
        try:
            raw_token = self.tokens.authenticate(username=self.username,
                                                 tenant_id=self.tenant_id,
                                                 tenant_name=self.tenant_name,
                                                 password=self.password,
                                                 token=self.auth_token,
                                                 return_raw=True)
            self._extract_service_catalog(self.auth_url, raw_token)
            return True
        except (exceptions.AuthorizationFailure, exceptions.Unauthorized):
            raise
        except Exception, e:
            _logger.exception("Authorization Failed.")
            raise exceptions.AuthorizationFailure("Authorization Failed: "
                                                  "%s" % e)

    def _extract_service_catalog(self, url, body):
        """ Set the client's service catalog from the response data. """
        self.service_catalog = service_catalog.ServiceCatalog(body)
        try:
            sc = self.service_catalog.get_token()
            self.auth_token = sc['id']
            # Save these since we have them and they'll be useful later
            # NOTE(termie): these used to be in the token and then were removed
            #               ... why?
            self.auth_tenant_id = sc.get('tenant_id')
            self.auth_user_id = sc.get('user_id')
        except KeyError:
            raise exceptions.AuthorizationFailure()

        # FIXME(ja): we should be lazy about setting managment_url.
        # in fact we should rewrite the client to support the service
        # catalog (api calls should be directable to any endpoints)
        try:
            self.management_url = self.service_catalog.url_for(attr='region',
                filter_value=self.region_name, endpoint_type='adminURL')
        except:
            # Unscoped tokens don't return a service catalog
            _logger.exception("unable to retrieve service catalog with token")
