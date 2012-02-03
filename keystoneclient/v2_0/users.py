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


class User(base.Resource):
    def __repr__(self):
        return "<User %s>" % self._info

    def delete(self):
        return self.manager.delete(self)

    def list_roles(self, tenant=None):
        return self.manager.list_roles(self.id, base.getid(tenant))


class UserManager(base.ManagerWithFind):
    resource_class = User

    def get(self, user):
        return self._get("/users/%s" % base.getid(user), "user")

    def update_email(self, user, email):
        """
        Update email
        """
        # FIXME(ja): why do we have to send id in params and url?
        params = {"user": {"id": base.getid(user),
                           "email": email}}

        return self._update("/users/%s" % base.getid(user), params, "user")

    def update_enabled(self, user, enabled):
        """
        Update enabled-ness
        """
        params = {"user": {"id": base.getid(user),
                           "enabled": enabled}}

        self._update("/users/%s/OS-KSADM/enabled" % base.getid(user), params,
                "user")

    def update_password(self, user, password):
        """
        Update password
        """
        params = {"passwordCredentials": {"username": user.name,
                                            "password": password}}

        return self._create("/users/%s/OS-KSADM/credentials/passwordCredentials"
                % base.getid(user), params, "passwordCredentials", return_raw=True)

    def update_tenant(self, user, tenant):
        """
        Update default tenant.
        """
        params = {"user": {"id": base.getid(user),
                           "tenantId": base.getid(tenant)}}

        return self._update("/users/%s/OS-KSADM/tenant" % base.getid(user),
                            params, "user")

    def create(self, name, password, email, tenant_id=None, enabled=True):
        """
        Create a user.
        """
        # FIXME(ja): email should be optional, keystone currently requires it
        params = {"user": {"name": name,
                           "password": password,
                           "tenantId": tenant_id,
                           "email": email,
                           "enabled": enabled}}
        return self._create('/users', params, "user")

    def delete(self, user):
        """
        Delete a user.
        """
        return self._delete("/users/%s" % base.getid(user))

    def list(self, tenant_id=None, limit=None, marker=None):
        """
        Get a list of users (optionally limited to a tenant)

        :rtype: list of :class:`User`
        """

        params = {}
        if limit:
            params['limit'] = int(limit)
        if marker:
            params['marker'] = int(marker)

        query = ""
        if params:
            query = "?" + urllib.urlencode(params)

        if not tenant_id:
            return self._list("/users%s" % query, "users")
        else:
            return self._list("/tenants/%s/users%s" % (tenant_id, query),
                              "users")

    def list_roles(self, user, tenant=None):
        return self.api.roles.roles_for_user(base.getid(user),
                                             base.getid(tenant))
