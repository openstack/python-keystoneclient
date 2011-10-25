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


class Role(base.Resource):
    def __repr__(self):
        return "<Role %s>" % self._info

    def delete(self):
        return self.manager.delete(self)


class RoleManager(base.ManagerWithFind):
    resource_class = Role

    def get(self, role):
        return self._get("/OS-KSADM/roles/%s" % base.getid(role), "role")

    def create(self, name):
        """
        Create a role.
        """
        params = {"role": {"name": name}}
        return self._create('/OS-KSADM/roles', params, "role")

    def delete(self, role):
        """
        Delete a role.
        """
        return self._delete("/OS-KSADM/roles/%s" % base.getid(role))

    def list(self):
        """
        List all available roles.
        """
        return self._list("/OS-KSADM/roles", "roles")

    # FIXME(ja): finialize roles once finalized in keystone
    #            right now the only way to add/remove a tenant is to
    #            give them a role within a project
    def get_user_role_refs(self, user_id):
        return self._list("/users/%s/roleRefs" % user_id, "roles")

    def add_user_to_tenant(self, tenant_id, user_id, role_id):
        params = {"role": {"tenantId": tenant_id, "roleId": role_id}}
        return self._create("/users/%s/roleRefs" % user_id, params, "role")

    def remove_user_from_tenant(self, tenant_id, user_id, role_id):
        params = {"role": {"tenantId": tenant_id, "roleId": role_id}}
        return self._delete("/users/%s/roleRefs/%s" % (user_id, role_id))
