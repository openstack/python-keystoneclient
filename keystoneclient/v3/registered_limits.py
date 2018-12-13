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


class RegisteredLimit(base.Resource):
    """Represents a registered limit.

    Attributes:
        * id: a UUID that identifies the registered limit
        * service_id: a UUID that identifies the service for the limit
        * region_id: a UUID that identifies the region for the limit
        * resource_name: the name of the resource to limit
        * default_limit: the default limit for projects to assume
        * description: a description of the registered limit

    """

    pass


class RegisteredLimitManager(base.CrudManager):
    """Manager class for registered limits."""

    resource_class = RegisteredLimit
    collection_key = 'registered_limits'
    key = 'registered_limit'

    def create(self, service, resource_name, default_limit,
               description=None, region=None, **kwargs):
        """Create a registered limit.

        :param service: a UUID that identifies the service for the limit.
        :type service: str
        :param resource_name: the name of the resource to limit.
        :type resource_name: str
        :param default_limit: the default limit for projects to assume.
        :type default_limit: int
        :param description: a string that describes the limit
        :type description: str
        :param region: a UUID that identifies the region for the limit.
        :type region: str

        :returns: a reference of the created registered limit.
        :rtype: :class:`keystoneclient.v3.registered_limits.RegisteredLimit`

        """
        # NOTE(lbragstad): Keystone's registered limit API supports creation of
        # limits in batches. This client accepts a single limit and passes it
        # to the identity service as a list of a single item.
        limit_data = base.filter_none(
            service_id=base.getid(service),
            resource_name=resource_name,
            default_limit=default_limit,
            description=description,
            region_id=base.getid(region),
            **kwargs
        )
        body = {self.collection_key: [limit_data]}
        resp, body = self.client.post('/registered_limits', body=body)
        registered_limit = body[self.collection_key].pop()
        return self._prepare_return_value(resp,
                                          self.resource_class(
                                              self, registered_limit))

    def update(self, registered_limit, service=None, resource_name=None,
               default_limit=None, description=None, region=None, **kwargs):
        """Update a registered limit.

        :param registered_limit:
            the UUID or reference of the registered limit to update.
        :param registered_limit:
            str or :class:`keystoneclient.v3.registered_limits.RegisteredLimit`
        :param service: a UUID that identifies the service for the limit.
        :type service: str
        :param resource_name: the name of the resource to limit.
        :type resource_name: str
        :param default_limit: the default limit for projects to assume.
        :type default_limit: int
        :param description: a string that describes the limit
        :type description: str
        :param region: a UUID that identifies the region for the limit.
        :type region: str

        :returns: a reference of the updated registered limit.
        :rtype: :class:`keystoneclient.v3.registered_limits.RegisteredLimit`

        """
        return super(RegisteredLimitManager, self).update(
            registered_limit_id=base.getid(registered_limit),
            service_id=base.getid(service),
            resource_name=resource_name,
            default_limit=default_limit,
            description=description,
            region=region,
            **kwargs
        )

    def get(self, registered_limit):
        """Retrieve a registered limit.

        :param registered_limit: the registered limit to get.
        :type registered_limit:
            str or :class:`keystoneclient.v3.registered_limits.RegisteredLimit`

        :returns: a specific registered limit.
        :rtype: :class:`keystoneclient.v3.registered_limits.RegisteredLimit`

        """
        return super(RegisteredLimitManager, self).get(
            registered_limit_id=base.getid(registered_limit))

    def list(self, service=None, resource_name=None, region=None, **kwargs):
        """List registered limits.

        Any parameter provided will be passed to the server as a filter.

        :param service: filter registered limits by service
        :type service: a UUID or :class:`keystoneclient.v3.services.Service`
        :param resource_name: filter registered limits by resource name
        :type resource_name: str
        :param region: filter registered limits by region
        :type region: a UUID or :class:`keystoneclient.v3.regions.Region`

        :returns: a list of registered limits.
        :rtype: list of
                :class:`keystoneclient.v3.registered_limits.RegisteredLimit`

        """
        return super(RegisteredLimitManager, self).list(
            service_id=base.getid(service),
            resource_name=resource_name,
            region_id=base.getid(region),
            **kwargs)

    def delete(self, registered_limit):
        """Delete a registered limit.

        :param registered_limit: the registered limit to delete.
        :type registered_limit:
            str or :class:`keystoneclient.v3.registered_limits.RegisteredLimit`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        registered_limit_id = base.getid(registered_limit)
        return super(RegisteredLimitManager, self).delete(
            registered_limit_id=registered_limit_id
        )
