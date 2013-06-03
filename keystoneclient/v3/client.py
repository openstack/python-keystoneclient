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
import json
import logging

from keystoneclient.v2_0 import client
from keystoneclient.v3 import credentials
from keystoneclient.v3 import endpoints
from keystoneclient.v3 import domains
from keystoneclient.v3 import groups
from keystoneclient.v3 import policies
from keystoneclient.v3 import projects
from keystoneclient.v3 import roles
from keystoneclient.v3 import services
from keystoneclient.v3 import users


_logger = logging.getLogger(__name__)


class Client(client.Client):
    """Client for the OpenStack Identity API v3.

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

        >>> from keystoneclient.v3 import client
        >>> keystone = client.Client(username=USER,
        ...                          password=PASS,
        ...                          tenant_name=TENANT_NAME,
        ...                          auth_url=KEYSTONE_URL)
        ...
        >>> keystone.tenants.list()
        ...
        >>> user = keystone.users.get(USER_ID)
        >>> user.delete()

    """

    def __init__(self, endpoint=None, **kwargs):
        """ Initialize a new client for the Keystone v3.0 API. """
        super(Client, self).__init__(endpoint=endpoint, **kwargs)

        self.credentials = credentials.CredentialManager(self)
        self.endpoints = endpoints.EndpointManager(self)
        self.domains = domains.DomainManager(self)
        self.groups = groups.GroupManager(self)
        self.policies = policies.PolicyManager(self)
        self.projects = projects.ProjectManager(self)
        self.roles = roles.RoleManager(self)
        self.services = services.ServiceManager(self)
        self.users = users.UserManager(self)

        # NOTE(gabriel): If we have a pre-defined endpoint then we can
        #                get away with lazy auth. Otherwise auth immediately.
        if endpoint:
            self.management_url = endpoint
        else:
            self.authenticate()

    def serialize(self, entity):
        return json.dumps(entity, sort_keys=True)
