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

from keystoneclient import base


class Group(base.Resource):
    """Represents an Identity user group.

    Attributes:
        * id: a uuid that identifies the group
        * name: group name
        * description: group description

    """

    def update(self, name=None, description=None):
        kwargs = {
            'name': name if name is not None else self.name,
            'description': (description
                            if description is not None
                            else self.description),
        }

        try:
            retval = self.manager.update(self.id, **kwargs)
            self = retval
        except Exception:
            retval = None

        return retval


class GroupManager(base.CrudManager):
    """Manager class for manipulating Identity groups."""

    resource_class = Group
    collection_key = 'groups'
    key = 'group'

    def create(self, name, domain=None, description=None, **kwargs):
        """Create a group.

        :param str name: the name of the group.
        :param domain: the domain of the group.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`
        :param str description: a description of the group.
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the created group returned from server.
        :rtype: :class:`keystoneclient.v3.groups.Group`

        """
        return super(GroupManager, self).create(
            name=name,
            domain_id=base.getid(domain),
            description=description,
            **kwargs)

    def list(self, user=None, domain=None, **kwargs):
        """List groups.

        :param user: the user of the groups to be filtered on.
        :type user: str or :class:`keystoneclient.v3.users.User`
        :param domain: the domain of the groups to be filtered on.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`
        :param kwargs: any other attribute provided will filter groups on.

        :returns: a list of groups.
        :rtype: list of :class:`keystoneclient.v3.groups.Group`.

        """
        if user:
            base_url = '/users/%s' % base.getid(user)
        else:
            base_url = None
        return super(GroupManager, self).list(
            base_url=base_url,
            domain_id=base.getid(domain),
            **kwargs)

    def get(self, group):
        """Retrieve a group.

        :param group: the group to be retrieved from the server.
        :type group: str or :class:`keystoneclient.v3.groups.Group`

        :returns: the specified group returned from server.
        :rtype: :class:`keystoneclient.v3.groups.Group`

        """
        return super(GroupManager, self).get(
            group_id=base.getid(group))

    def update(self, group, name=None, description=None, **kwargs):
        """Update a group.

        :param group: the group to be updated on the server.
        :type group: str or :class:`keystoneclient.v3.groups.Group`
        :param str name: the new name of the group.
        :param str description: the new description of the group.
        :param kwargs: any other attribute provided will be passed to server.

        :returns: the updated group returned from server.
        :rtype: :class:`keystoneclient.v3.groups.Group`

        """
        return super(GroupManager, self).update(
            group_id=base.getid(group),
            name=name,
            description=description,
            **kwargs)

    def delete(self, group):
        """Delete a group.

        :param group: the group to be deleted on the server.
        :type group: str or :class:`keystoneclient.v3.groups.Group`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        return super(GroupManager, self).delete(
            group_id=base.getid(group))
