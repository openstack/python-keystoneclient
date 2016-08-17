# Copyright 2011 OpenStack Foundation
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

from debtcollector import renames
from positional import positional

from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient.i18n import _


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
            msg = _('Specify both a user and a group')
            raise exceptions.ValidationError(msg)

    @renames.renamed_kwarg('project', 'default_project', version='1.7.0',
                           removal_version='2.0.0')
    @positional(1, enforcement=positional.WARN)
    def create(self, name, domain=None, project=None, password=None,
               email=None, description=None, enabled=True,
               default_project=None, **kwargs):
        """Create a user.

        :param str name: the name of the user.
        :param domain: the domain of the user.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`
        :param project: the default project of the user.
                        (deprecated, see warning below)
        :type project: str or :class:`keystoneclient.v3.projects.Project`
        :param str password: the password for the user.
        :param str email: the email address of the user.
        :param str description: a description of the user.
        :param bool enabled: whether the user is enabled.
        :param default_project: the default project of the user.
        :type default_project: str or
                               :class:`keystoneclient.v3.projects.Project`
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the created user returned from server.
        :rtype: :class:`keystoneclient.v3.users.User`

        .. warning::

          The project argument is deprecated as of the 1.7.0 release in favor
          of default_project and may be removed in the 2.0.0 release.

          If both default_project and project is provided, the default_project
          will be used.

        """
        default_project_id = base.getid(default_project) or base.getid(project)
        user_data = base.filter_none(name=name,
                                     domain_id=base.getid(domain),
                                     default_project_id=default_project_id,
                                     password=password,
                                     email=email,
                                     description=description,
                                     enabled=enabled,
                                     **kwargs)

        return self._post('/users', {'user': user_data}, 'user',
                          log=not bool(password))

    @renames.renamed_kwarg('project', 'default_project', version='1.7.0',
                           removal_version='2.0.0')
    @positional(enforcement=positional.WARN)
    def list(self, project=None, domain=None, group=None, default_project=None,
             **kwargs):
        """List users.

        :param project: the default project of the users to be filtered on.
                        (deprecated, see warning below)
        :type project: str or :class:`keystoneclient.v3.projects.Project`
        :param domain: the domain of the users to be filtered on.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`
        :param group: the group in which the users are member of.
        :type group: str or :class:`keystoneclient.v3.groups.Group`
        :param default_project: the default project of the users to be filtered
                                on.
        :type default_project: str or
                               :class:`keystoneclient.v3.projects.Project`
        :param kwargs: any other attribute provided will filter users on.

        :returns: a list of users.
        :rtype: list of :class:`keystoneclient.v3.users.User`.

        .. warning::

          The project argument is deprecated as of the 1.7.0 release in favor
          of default_project and may be removed in the 2.0.0 release.

          If both default_project and project is provided, the default_project
          will be used.

        """
        default_project_id = base.getid(default_project) or base.getid(project)
        if group:
            base_url = '/groups/%s' % base.getid(group)
        else:
            base_url = None

        return super(UserManager, self).list(
            base_url=base_url,
            domain_id=base.getid(domain),
            default_project_id=default_project_id,
            **kwargs)

    def get(self, user):
        """Retrieve a user.

        :param user: the user to be retrieved from the server.
        :type user: str or :class:`keystoneclient.v3.users.User`

        :returns: the specified user returned from server.
        :rtype: :class:`keystoneclient.v3.users.User`

        """
        return super(UserManager, self).get(
            user_id=base.getid(user))

    @renames.renamed_kwarg('project', 'default_project', version='1.7.0',
                           removal_version='2.0.0')
    @positional(enforcement=positional.WARN)
    def update(self, user, name=None, domain=None, project=None, password=None,
               email=None, description=None, enabled=None,
               default_project=None, **kwargs):
        """Update a user.

        :param user: the user to be updated on the server.
        :type user: str or :class:`keystoneclient.v3.users.User`
        :param str name: the new name of the user.
        :param domain: the new domain of the user.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`
        :param project: the new default project of the user.
                        (deprecated, see warning below)
        :type project: str or :class:`keystoneclient.v3.projects.Project`
        :param str password: the new password of the user.
        :param str email: the new email of the user.
        :param str description: the newdescription of the user.
        :param bool enabled: whether the user is enabled.
        :param default_project: the new default project of the user.
        :type default_project: str or
                               :class:`keystoneclient.v3.projects.Project`
        :param kwargs: any other attribute provided will be passed to server.

        :returns: the updated user returned from server.
        :rtype: :class:`keystoneclient.v3.users.User`

        .. warning::

          The project argument is deprecated as of the 1.7.0 release in favor
          of default_project and may be removed in the 2.0.0 release.

          If both default_project and project is provided, the default_project
          will be used.

        """
        default_project_id = base.getid(default_project) or base.getid(project)
        user_data = base.filter_none(name=name,
                                     domain_id=base.getid(domain),
                                     default_project_id=default_project_id,
                                     password=password,
                                     email=email,
                                     description=description,
                                     enabled=enabled,
                                     **kwargs)

        return self._update('/users/%s' % base.getid(user),
                            {'user': user_data},
                            'user',
                            method='PATCH',
                            log=False)

    def update_password(self, old_password, new_password):
        """Update the password for the user the token belongs to.

        :param str old_password: the user's old password
        :param str new_password: the user's new password

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        if not (old_password and new_password):
            msg = _('Specify both the current password and a new password')
            raise exceptions.ValidationError(msg)

        if old_password == new_password:
            msg = _('Old password and new password must be different.')
            raise exceptions.ValidationError(msg)

        params = {'user': {'password': new_password,
                           'original_password': old_password}}

        base_url = '/users/%s/password' % self.client.user_id

        return self._update(base_url, params, method='POST', log=False)

    def add_to_group(self, user, group):
        """Add the specified user as a member of the specified group.

        :param user: the user to be added to the group.
        :type user: str or :class:`keystoneclient.v3.users.User`
        :param group: the group to put the user in.
        :type group: str or :class:`keystoneclient.v3.groups.Group`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).put(
            base_url=base_url,
            user_id=base.getid(user))

    def check_in_group(self, user, group):
        """Check if the specified user is a member of the specified group.

        :param user: the user to be verified in the group.
        :type user: str or :class:`keystoneclient.v3.users.User`
        :param group: the group to check the user in.
        :type group: str or :class:`keystoneclient.v3.groups.Group`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).head(
            base_url=base_url,
            user_id=base.getid(user))

    def remove_from_group(self, user, group):
        """Remove the specified user from the specified group.

        :param user: the user to be removed from the group.
        :type user: str or :class:`keystoneclient.v3.users.User`
        :param group: the group to remove the user from.
        :type group: str or :class:`keystoneclient.v3.groups.Group`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).delete(
            base_url=base_url,
            user_id=base.getid(user))

    def delete(self, user):
        """Delete a user.

        :param user: the user to be deleted on the server.
        :type user: str or :class:`keystoneclient.v3.users.User`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        return super(UserManager, self).delete(
            user_id=base.getid(user))
