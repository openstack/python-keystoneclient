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


class RoleAssignment(base.Resource):

    """Represents an Identity role assignment.

    Attributes:
        * role: an object which contains a role uuid
        * user or group: an object which contains either a user or
                         group uuid
        * scope: an object which has either a project or domain object
                 containing an uuid
    """
    pass


class RoleAssignmentManager(base.CrudManager):

    """Manager class for manipulating Identity roles assignments."""
    resource_class = RoleAssignment
    collection_key = 'role_assignments'
    key = 'role_assignment'

    def _check_not_user_and_group(self, user, group):
        if user and group:
            msg = 'Specify either a user or group, not both'
            raise exceptions.ValidationError(msg)

    def _check_not_domain_and_project(self, domain, project):
        if domain and project:
            msg = 'Specify either a domain or project, not both'
            raise exceptions.ValidationError(msg)

    def list(self, user=None, group=None, project=None, domain=None, role=None,
             effective=False):
        """Lists role assignments.

        If no arguments are provided, all role assignments in the
        system will be listed.

        If both user and group are provided, a ValidationError will be
        raised. If both domain and project are provided, it will also
        raise a ValidationError.

        :param user: User to be used as query filter. (optional)
        :param group: Group to be used as query filter. (optional)
        :param project: Project to be used as query filter.
                        (optional)
        :param domain: Domain to be used as query
                       filter. (optional)
        :param role: Role to be used as query filter. (optional)
        :param boolean effective: return effective role
                                  assignments. (optional)
        """

        self._check_not_user_and_group(user, group)
        self._check_not_domain_and_project(domain, project)

        query_params = {}
        if user:
            query_params['user.id'] = base.getid(user)
        if group:
            query_params['group.id'] = base.getid(group)
        if project:
            query_params['scope.project.id'] = base.getid(project)
        if domain:
            query_params['scope.domain.id'] = base.getid(domain)
        if role:
            query_params['role.id'] = base.getid(role)
        if effective:
            query_params['effective'] = effective

        return super(RoleAssignmentManager, self).list(**query_params)

    def create(self, **kwargs):
        raise exceptions.MethodNotImplemented('Create not supported for'
                                              ' role assignments')

    def update(self, **kwargs):
        raise exceptions.MethodNotImplemented('Update not supported for'
                                              ' role assignments')

    def get(self, **kwargs):
        raise exceptions.MethodNotImplemented('Get not supported for'
                                              ' role assignments')

    def find(self, **kwargs):
        raise exceptions.MethodNotImplemented('Find not supported for'
                                              ' role assignments')

    def put(self, **kwargs):
        raise exceptions.MethodNotImplemented('Put not supported for'
                                              ' role assignments')

    def delete(self, **kwargs):
        raise exceptions.MethodNotImplemented('Delete not supported for'
                                              ' role assignments')
