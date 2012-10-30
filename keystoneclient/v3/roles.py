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
from keystoneclient import exceptions


class Role(base.Resource):
    """Represents an Identity role.

    Attributes:
        * id: a uuid that identifies the role
        * name: user-facing identifier

    """
    pass


class RoleManager(base.CrudManager):
    """Manager class for manipulating Identity roles."""
    resource_class = Role
    collection_key = 'roles'
    key = 'role'

    def _role_grants_base_url(self, user, domain, project):
        params = {'user_id': base.getid(user)}

        if domain:
            params['domain_id'] = base.getid(domain)
            base_url = '/domains/%(domain_id)s/users/%(user_id)s'
        elif project:
            params['project_id'] = base.getid(project)
            base_url = '/projects/%(project_id)s/users/%(user_id)s'

        return base_url % params

    def _require_domain_or_project(self, domain, project):
        if (domain and project) or (not domain and not project):
            msg = 'Specify either a domain or project, not both'
            raise exceptions.ValidationError(msg)

    def create(self, name):
        return super(RoleManager, self).create(
            name=name)

    def get(self, role):
        return super(RoleManager, self).get(
            role_id=base.getid(role))

    def list(self, user=None, domain=None, project=None):
        """Lists roles and role grants.

        If no arguments are provided, all roles in the system will be listed.

        If a user is specified, you must also specify either a domain or
        project to list role grants on that pair.
        """

        if user:
            self._require_domain_or_project(domain, project)
            return super(RoleManager, self).list(
                base_url=self._role_grants_base_url(user, domain, project))

        return super(RoleManager, self).list()

    def update(self, role, name=None):
        return super(RoleManager, self).update(
            role_id=base.getid(role),
            name=name)

    def delete(self, role):
        return super(RoleManager, self).delete(
            role_id=base.getid(role))

    def grant(self, role, user, domain=None, project=None):
        """Grants a role to a user on either a domain or project."""
        self._require_domain_or_project(domain, project)

        return super(RoleManager, self).put(
            base_url=self._role_grants_base_url(user, domain, project),
            role_id=base.getid(role))

    def check(self, role, user, domain=None, project=None):
        """Grants a role to a user on either a domain or project."""
        self._require_domain_or_project(domain, project)

        return super(RoleManager, self).head(
            base_url=self._role_grants_base_url(user, domain, project),
            role_id=base.getid(role))

    def revoke(self, role, user, domain=None, project=None):
        """Revokes a role from a user on either a domain or project."""
        self._require_domain_or_project(domain, project)

        return super(RoleManager, self).delete(
            base_url=self._role_grants_base_url(user, domain, project),
            role_id=base.getid(role))
