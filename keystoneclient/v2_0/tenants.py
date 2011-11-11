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

from keystoneclient import base


class Tenant(base.Resource):
    def __repr__(self):
        return "<Tenant %s>" % self._info

    def delete(self):
        return self.manager.delete(self)

    def update(self, description=None, enabled=None):
        # FIXME(ja): set the attributes in this object if successful
        return self.manager.update(self.id, description, enabled)

    def add_user(self, user):
        return self.manager.add_user_to_tenant(self.id, base.getid(user))


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

    def list(self):
        """
        Get a list of tenants.
        :rtype: list of :class:`Tenant`
        """
        return self._list("/tenants", "tenants")

    def update(self, tenant_id, tenant_name=None, description=None,
               enabled=None):
        """
        update a tenant with a new name and description
        """
        body = {"tenant": {'id': tenant_id}}
        if tenant_name is not None:
            body['tenant']['name'] = tenant_name
        if enabled is not None:
            body['tenant']['enabled'] = enabled
        if description:
            body['tenant']['description'] = description

        return self._update("/tenants/%s" % tenant_id, body, "tenant")

    def delete(self, tenant):
        """
        Delete a tenant.
        """
        return self._delete("/tenants/%s" % (base.getid(tenant)))
