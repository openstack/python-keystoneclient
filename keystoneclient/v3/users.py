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


class User(base.Resource):
    """Represents an Identity user.

    Attributes:
        * id: a uuid that identifies the user

    """
    pass


class UserManager(base.CrudManager):
    """Manager class for manipulating Identity users."""
    resource_class = User
    collection_key = 'users'
    key = 'user'

    def _require_user_and_group(self, user, group):
        if not (user and group):
            msg = 'Specify both a user and a group'
            raise exceptions.ValidationError(msg)

    def create(self, name, domain=None, project=None, password=None,
               email=None, description=None, enabled=True):
        return super(UserManager, self).create(
            name=name,
            domain_id=base.getid(domain),
            project_id=base.getid(project),
            password=password,
            email=email,
            description=description,
            enabled=enabled)

    def list(self, project=None, domain=None, group=None, **kwargs):
        """List users.

        If project, domain or group are provided, then filter
        users with those attributes.

        If ``**kwargs`` are provided, then filter users with
        attributes matching ``**kwargs``.
        """
        if group:
            base_url = '/groups/%s' % base.getid(group)
        else:
            base_url = None

        return super(UserManager, self).list(
            base_url=base_url,
            domain_id=base.getid(domain),
            project_id=base.getid(project),
            **kwargs)

    def get(self, user):
        return super(UserManager, self).get(
            user_id=base.getid(user))

    def update(self, user, name=None, domain=None, project=None, password=None,
               email=None, description=None, enabled=None):
        return super(UserManager, self).update(
            user_id=base.getid(user),
            name=name,
            domain_id=base.getid(domain),
            project_id=base.getid(project),
            password=password,
            email=email,
            description=description,
            enabled=enabled)

    def add_to_group(self, user, group):
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).put(
            base_url=base_url,
            user_id=base.getid(user))

    def check_in_group(self, user, group):
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).head(
            base_url=base_url,
            user_id=base.getid(user))

    def remove_from_group(self, user, group):
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).delete(
            base_url=base_url,
            user_id=base.getid(user))

    def delete(self, user):
        return super(UserManager, self).delete(
            user_id=base.getid(user))
