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

import abc

from keystoneauth1 import exceptions
from keystoneauth1 import plugin
import six

from keystoneclient import base


@six.add_metaclass(abc.ABCMeta)
class EntityManager(base.Manager):
    """Manager class for listing federated accessible objects."""

    resource_class = None

    @abc.abstractproperty
    def object_type(self):
        raise exceptions.MethodNotImplemented

    def list(self):
        url = '/auth/%s' % self.object_type
        try:
            tenant_list = self._list(url, self.object_type)
        except exceptions.CatalogException:
            endpoint_filter = {'interface': plugin.AUTH_INTERFACE}
            tenant_list = self._list(url, self.object_type,
                                     endpoint_filter=endpoint_filter)
        return tenant_list
