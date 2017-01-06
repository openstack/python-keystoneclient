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


class EndpointGroup(base.Resource):
    """Represents an identity endpoint group.

    Attributes:
        * id: a UUID that identifies the endpoint group
        * name: the endpoint group name
        * description: the endpoint group description
        * filters: representation of filters in the format of JSON that define
                   what endpoint entities are part of the group

    """

    pass


class EndpointGroupManager(base.CrudManager):
    """Manager class for Endpoint Groups."""

    resource_class = EndpointGroup
    collection_key = 'endpoint_groups'
    key = 'endpoint_group'
    base_url = 'OS-EP-FILTER'

    def create(self, name, filters, description=None, **kwargs):
        """Create an endpoint group.

        :param str name: the name of the endpoint group.
        :param str filters: representation of filters in the format of JSON
                            that define what endpoint entities are part of the
                            group.
        :param str description: a description of the endpoint group.
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the created endpoint group returned from server.
        :rtype: :class:`keystoneclient.v3.endpoint_groups.EndpointGroup`

        """
        return super(EndpointGroupManager, self).create(
            name=name,
            filters=filters,
            description=description,
            **kwargs)

    def get(self, endpoint_group):
        """Retrieve an endpoint group.

        :param endpoint_group: the endpoint group to be retrieved from the
                               server.
        :type endpoint_group:
            str or :class:`keystoneclient.v3.endpoint_groups.EndpointGroup`

        :returns: the specified endpoint group returned from server.
        :rtype: :class:`keystoneclient.v3.endpoint_groups.EndpointGroup`

        """
        return super(EndpointGroupManager, self).get(
            endpoint_group_id=base.getid(endpoint_group))

    def check(self, endpoint_group):
        """Check if an endpoint group exists.

        :param endpoint_group: the endpoint group to be checked against the
                               server.
        :type endpoint_group:
            str or :class:`keystoneclient.v3.endpoint_groups.EndpointGroup`

        :returns: none if the specified endpoint group exists.

        """
        return super(EndpointGroupManager, self).head(
            endpoint_group_id=base.getid(endpoint_group))

    def list(self, **kwargs):
        """List endpoint groups.

        Any parameter provided will be passed to the server.

        :returns: a list of endpoint groups.
        :rtype: list of
                :class:`keystoneclient.v3.endpoint_groups.EndpointGroup`.

        """
        return super(EndpointGroupManager, self).list(**kwargs)

    def update(self, endpoint_group, name=None, filters=None,
               description=None, **kwargs):
        """Update an endpoint group.

        :param str name: the new name of the endpoint group.
        :param str filters: the new representation of filters in the format of
                            JSON that define what endpoint entities are part of
                            the group.
        :param str description: the new description of the endpoint group.
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the updated endpoint group returned from server.
        :rtype: :class:`keystoneclient.v3.endpoint_groups.EndpointGroup`

        """
        return super(EndpointGroupManager, self).update(
            endpoint_group_id=base.getid(endpoint_group),
            name=name,
            filters=filters,
            description=description,
            **kwargs)

    def delete(self, endpoint_group):
        """Delete an endpoint group.

        :param endpoint_group: the endpoint group to be deleted on the server.
        :type endpoint_group:
            str or :class:`keystoneclient.v3.endpoint_groups.EndpointGroup`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        return super(EndpointGroupManager, self).delete(
            endpoint_group_id=base.getid(endpoint_group))
