# Copyright 2011 OpenStack LLC.
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

import urllib

from keystoneclient import base


class Tenant(base.Resource):
    def __repr__(self):
        return "<Tenant %s>" % self._info

    def delete(self):
        return self.manager.delete(self)

    def update(self, name=None, description=None, enabled=None):
        # Preserve the existing settings; keystone legacy resets these?
        new_name = name if name else self.name
        new_description = description if description else self.description
        new_enabled = enabled if enabled else self.enabled

        try:
            retval = self.manager.update(self.id, tenant_name=new_name,
                                         description=new_description,
                                         enabled=new_enabled)
            self = retval
        except Exception, e:
            retval = None
        return retval

    def add_user(self, user, role):
        return self.manager.api.roles.add_user_role(base.getid(user),
                                                    base.getid(role),
                                                    self.id)

    def remove_user(self, user, role):
        return self.manager.api.roles.remove_user_role(base.getid(user),
                                                      base.getid(role),
                                                      self.id)

    def list_users(self):
        return self.manager.list_users(self.id)


class TenantManager(base.ManagerWithFind):
    resource_class = Tenant

    def get(self, tenant_id):
        return self._get("/tenants/%s" % tenant_id, "tenant")

    def create(self, tenant_name, description=None, enabled=True):
        """
        Create a new tenant.
        """
        params = {"tenant": {"name": tenant_name,
                             "description": description,
                             "enabled": enabled}}

        return self._create('/tenants', params, "tenant")

    def list(self, limit=None, marker=None):
        """
        Get a list of tenants.
        :rtype: list of :class:`Tenant`
        """

        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker

        query = ""
        if params:
            query = "?" + urllib.urlencode(params)

        return self._list("/tenants%s" % query, "tenants")

    def update(self, tenant_id, tenant_name=None, description=None,
               enabled=None):
        """
        Update a tenant with a new name and description.
        """
        body = {"tenant": {'id': tenant_id}}
        if tenant_name is not None:
            body['tenant']['name'] = tenant_name
        if enabled is not None:
            body['tenant']['enabled'] = enabled
        if description:
            body['tenant']['description'] = description
        # Keystone's API uses a POST rather than a PUT here.
        return self._create("/tenants/%s" % tenant_id, body, "tenant")

    def delete(self, tenant):
        """
        Delete a tenant.
        """
        return self._delete("/tenants/%s" % (base.getid(tenant)))

    def list_users(self, tenant):
        """ List users for a tenant. """
        return self.api.users.list(base.getid(tenant))

    def add_user(self, tenant, user, role):
        """ Add a user to a tenant with the given role. """
        return self.api.roles.add_user_role(base.getid(user),
                                            base.getid(role),
                                            base.getid(tenant))

    def remove_user(self, tenant, user, role):
        """ Remove the specified role from the user on the tenant. """
        return self.api.roles.remove_user_role(base.getid(user),
                                               base.getid(role),
                                               base.getid(tenant))
