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

from positional import positional

from keystoneclient import base


class Service(base.Resource):
    """Represents an Identity service.

    Attributes:
        * id: a uuid that identifies the service
        * name: the user-facing name of the service (e.g. Keystone)
        * description: a description of the service
        * type: the type of the service (e.g. 'compute', 'identity')
        * enabled: determines whether the service appears in the catalog

    """

    pass


class ServiceManager(base.CrudManager):
    """Manager class for manipulating Identity services."""

    resource_class = Service
    collection_key = 'services'
    key = 'service'

    @positional(1, enforcement=positional.WARN)
    def create(self, name, type=None,
               enabled=True, description=None, **kwargs):
        """Create a service.

        :param str name: the name of the service.
        :param str type: the type of the service.
        :param bool enabled: whether the service appears in the catalog.
        :param str description: the description of the service.
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the created service returned from server.
        :rtype: :class:`keystoneclient.v3.services.Service`

        """
        type_arg = type or kwargs.pop('service_type', None)
        return super(ServiceManager, self).create(
            name=name,
            type=type_arg,
            description=description,
            enabled=enabled,
            **kwargs)

    def get(self, service):
        """Retrieve a service.

        :param service: the service to be retrieved from the server.
        :type service: str or :class:`keystoneclient.v3.services.Service`

        :returns: the specified service returned from server.
        :rtype: :class:`keystoneclient.v3.services.Service`

        """
        return super(ServiceManager, self).get(
            service_id=base.getid(service))

    @positional(enforcement=positional.WARN)
    def list(self, name=None, type=None, **kwargs):
        """List services.

        :param str name: the name of the services to be filtered on.
        :param str type: the type of the services to be filtered on.
        :param kwargs: any other attribute provided will filter services on.

        :returns: a list of services.
        :rtype: list of :class:`keystoneclient.v3.services.Service`

        """
        type_arg = type or kwargs.pop('service_type', None)
        return super(ServiceManager, self).list(
            name=name,
            type=type_arg,
            **kwargs)

    @positional(enforcement=positional.WARN)
    def update(self, service, name=None, type=None, enabled=None,
               description=None, **kwargs):
        """Update a service.

        :param service: the service to be updated on the server.
        :type service: str or :class:`keystoneclient.v3.services.Service`
        :param str name: the new name of the service.
        :param str type: the new type of the service.
        :param bool enabled: whether the service appears in the catalog.
        :param str description: the new description of the service.
        :param kwargs: any other attribute provided will be passed to server.

        :returns: the updated service returned from server.
        :rtype: :class:`keystoneclient.v3.services.Service`

        """
        type_arg = type or kwargs.pop('service_type', None)
        return super(ServiceManager, self).update(
            service_id=base.getid(service),
            name=name,
            type=type_arg,
            description=description,
            enabled=enabled,
            **kwargs)

    def delete(self, service=None, id=None):
        """Delete a service.

        :param service: the service to be deleted on the server.
        :type service: str or :class:`keystoneclient.v3.services.Service`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        if service:
            service_id = base.getid(service)
        else:
            service_id = id
        return super(ServiceManager, self).delete(
            service_id=service_id)
