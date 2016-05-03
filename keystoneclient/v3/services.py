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
        * name: user-facing name of the service (e.g. Keystone)
        * type: 'compute', 'identity', etc
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
        type_arg = type or kwargs.pop('service_type', None)
        return super(ServiceManager, self).create(
            name=name,
            type=type_arg,
            description=description,
            enabled=enabled,
            **kwargs)

    def get(self, service):
        return super(ServiceManager, self).get(
            service_id=base.getid(service))

    @positional(enforcement=positional.WARN)
    def list(self, name=None, type=None, **kwargs):
        type_arg = type or kwargs.pop('service_type', None)
        return super(ServiceManager, self).list(
            name=name,
            type=type_arg,
            **kwargs)

    @positional(enforcement=positional.WARN)
    def update(self, service, name=None, type=None, enabled=None,
               description=None, **kwargs):
        type_arg = type or kwargs.pop('service_type', None)
        return super(ServiceManager, self).update(
            service_id=base.getid(service),
            name=name,
            type=type_arg,
            description=description,
            enabled=enabled,
            **kwargs)

    def delete(self, service=None, id=None):
        if service:
            service_id = base.getid(service)
        else:
            service_id = id
        return super(ServiceManager, self).delete(
            service_id=service_id)
