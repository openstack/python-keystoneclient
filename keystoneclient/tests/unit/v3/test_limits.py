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

from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import limits


class LimitTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(LimitTests, self).setUp()
        self.key = 'limit'
        self.collection_key = 'limits'
        self.model = limits.Limit
        self.manager = self.client.limits

    def new_ref(self, **kwargs):
        ref = {
            'id': uuid.uuid4().hex,
            'project_id': uuid.uuid4().hex,
            'service_id': uuid.uuid4().hex,
            'resource_name': uuid.uuid4().hex,
            'resource_limit': 15,
            'description': uuid.uuid4().hex
        }
        ref.update(kwargs)
        return ref

    def test_create(self):
        # This test overrides the generic test case provided by the CrudTests
        # class because the limits API supports creating multiple limits in a
        # single POST request. As a result, it returns the limits as a list of
        # all the created limits from the request. This is different from what
        # the base test_create() method assumes about keystone's API. The
        # changes here override the base test to closely model how the actual
        # limit API behaves.
        ref = self.new_ref()
        manager_ref = ref.copy()
        manager_ref.pop('id')
        req_ref = [manager_ref.copy()]

        self.stub_entity('POST', entity=req_ref, status_code=201)

        returned = self.manager.create(**utils.parameterize(manager_ref))
        self.assertIsInstance(returned, self.model)

        expected_limit = req_ref.pop()
        for attr in expected_limit:
            self.assertEqual(
                getattr(returned, attr),
                expected_limit[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs([expected_limit])

    def test_list_filter_by_service(self):
        service_id = uuid.uuid4().hex
        expected_query = {'service_id': service_id}
        self.test_list(expected_query=expected_query, service=service_id)

    def test_list_filtered_by_resource_name(self):
        resource_name = uuid.uuid4().hex
        self.test_list(resource_name=resource_name)

    def test_list_filtered_by_region(self):
        region_id = uuid.uuid4().hex
        expected_query = {'region_id': region_id}
        self.test_list(expected_query=expected_query, region=region_id)
