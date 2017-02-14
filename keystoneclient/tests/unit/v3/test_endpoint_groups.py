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

import uuid

from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import endpoint_groups


class EndpointGroupTests(utils.ClientTestCase, utils.CrudTests):

    def setUp(self):
        super(EndpointGroupTests, self).setUp()
        self.key = 'endpoint_group'
        self.collection_key = 'endpoint_groups'
        self.model = endpoint_groups.EndpointGroup
        self.manager = self.client.endpoint_groups
        self.path_prefix = 'OS-EP-FILTER'

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('filters', '{"interface": "public"}')
        kwargs.setdefault('description', uuid.uuid4().hex)
        return kwargs
