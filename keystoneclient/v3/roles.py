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

    def create(self, name):
        return super(RoleManager, self).create(
            name=name)

    def get(self, role):
        return super(RoleManager, self).get(
            role_id=base.getid(role))

    def update(self, role, name=None):
        return super(RoleManager, self).update(
            role_id=base.getid(role),
            name=name)

    def delete(self, role):
        return super(RoleManager, self).delete(
            role_id=base.getid(role))
