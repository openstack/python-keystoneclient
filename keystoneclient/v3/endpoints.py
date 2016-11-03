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
from keystoneclient import exceptions
from keystoneclient.i18n import _


VALID_INTERFACES = ['public', 'admin', 'internal']


class Endpoint(base.Resource):
    """Represents an Identity endpoint.

    Attributes:
        * id: a uuid that identifies the endpoint
        * interface: 'public', 'admin' or 'internal' network interface
        * region: geographic location of the endpoint
        * service_id: service to which the endpoint belongs
        * url: fully qualified service endpoint
        * enabled: determines whether the endpoint appears in the service
                   catalog

    """

    pass


class EndpointManager(base.CrudManager):
    """Manager class for manipulating Identity endpoints."""

    resource_class = Endpoint
    collection_key = 'endpoints'
    key = 'endpoint'

    def _validate_interface(self, interface):
        if interface is not None and interface not in VALID_INTERFACES:
            msg = _('"interface" must be one of: %s')
            msg %= ', '.join(VALID_INTERFACES)
            raise exceptions.ValidationError(msg)

    @positional(1, enforcement=positional.WARN)
    def create(self, service, url, interface=None, region=None, enabled=True,
               **kwargs):
        """Create an endpoint.

        :param service: the service to which the endpoint belongs.
        :type service: str or :class:`keystoneclient.v3.services.Service`
        :param str url: the URL of the fully qualified service endpoint.
        :param str interface: the network interface of the endpoint. Valid
                             values are: ``public``, ``admin`` or ``internal``.
        :param region: the region to which the endpoint belongs.
        :type region: str or :class:`keystoneclient.v3.regions.Region`
        :param bool enabled: whether the endpoint is enabled or not,
                             determining if it appears in the service catalog.
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the created endpoint returned from server.
        :rtype: :class:`keystoneclient.v3.endpoints.Endpoint`

        """
        self._validate_interface(interface)
        return super(EndpointManager, self).create(
            service_id=base.getid(service),
            interface=interface,
            url=url,
            region=region,
            enabled=enabled,
            **kwargs)

    def get(self, endpoint):
        """Retrieve an endpoint.

        :param endpoint: the endpoint to be retrieved from the server.
        :type endpoint: str or :class:`keystoneclient.v3.endpoints.Endpoint`

        :returns: the specified endpoint returned from server.
        :rtype: :class:`keystoneclient.v3.endpoints.Endpoint`

        """
        return super(EndpointManager, self).get(
            endpoint_id=base.getid(endpoint))

    @positional(enforcement=positional.WARN)
    def list(self, service=None, interface=None, region=None, enabled=None,
             region_id=None, **kwargs):
        """List endpoints.

        :param service: the service of the endpoints to be filtered on.
        :type service: str or :class:`keystoneclient.v3.services.Service`
        :param str interface: the network interface of the endpoints to be
                              filtered on. Valid values are: ``public``,
                              ``admin`` or ``internal``.
        :param bool enabled: whether to return enabled or disabled endpoints.
        :param str region_id: filter endpoints by the region_id attribute. If
                              both region and region_id are specified, region
                              takes precedence.
        :param kwargs: any other attribute provided will filter endpoints on.

        :returns: a list of endpoints.
        :rtype: list of :class:`keystoneclient.v3.endpoints.Endpoint`

        """
        # NOTE(lhcheng): region filter is not supported by keystone,
        # region_id should be used instead. Consider removing the
        # region argument in the next release.
        self._validate_interface(interface)
        return super(EndpointManager, self).list(
            service_id=base.getid(service),
            interface=interface,
            region_id=region_id or base.getid(region),
            enabled=enabled,
            **kwargs)

    @positional(enforcement=positional.WARN)
    def update(self, endpoint, service=None, url=None, interface=None,
               region=None, enabled=None, **kwargs):
        """Update an endpoint.

        :param endpoint: the endpoint to be updated on the server.
        :type endpoint: str or :class:`keystoneclient.v3.endpoints.Endpoint`
        :param service: the new service to which the endpoint belongs.
        :type service: str or :class:`keystoneclient.v3.services.Service`
        :param str url: the new URL of the fully qualified service endpoint.
        :param str interface: the new network interface of the endpoint. Valid
                             values are: ``public``, ``admin`` or ``internal``.
        :param region: the new region to which the endpoint belongs.
        :type region: str or :class:`keystoneclient.v3.regions.Region`
        :param bool enabled: determining if the endpoint appears in the service
                             catalog by enabling or disabling it.
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the updated endpoint returned from server.
        :rtype: :class:`keystoneclient.v3.endpoints.Endpoint`

        """
        self._validate_interface(interface)
        return super(EndpointManager, self).update(
            endpoint_id=base.getid(endpoint),
            service_id=base.getid(service),
            interface=interface,
            url=url,
            region=region,
            enabled=enabled,
            **kwargs)

    def delete(self, endpoint):
        """Delete an endpoint.

        :param endpoint: the endpoint to be deleted on the server.
        :type endpoint: str or :class:`keystoneclient.v3.endpoints.Endpoint`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        return super(EndpointManager, self).delete(
            endpoint_id=base.getid(endpoint))
