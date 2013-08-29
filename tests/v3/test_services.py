# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from keystoneclient.v3 import services
from tests.v3 import utils


class ServiceTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(ServiceTests, self).setUp()
        self.key = 'service'
        self.collection_key = 'services'
        self.model = services.Service
        self.manager = self.client.services

    def new_ref(self, **kwargs):
        kwargs = super(ServiceTests, self).new_ref(**kwargs)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('type', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        return kwargs
