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

from keystoneauth1.exceptions import http

from keystoneclient.tests.functional import base
from keystoneclient.tests.functional.v3 import client_fixtures as fixtures


class EndpointGroupsTestMixin(object):

    def check_endpoint_group(self, endpoint_group, endpoint_group_ref=None):
        self.assertIsNotNone(endpoint_group.id)
        self.assertIn('self', endpoint_group.links)
        self.assertIn('/endpoint_groups/' + endpoint_group.id,
                      endpoint_group.links['self'])

        if endpoint_group_ref:
            self.assertEqual(endpoint_group_ref['name'], endpoint_group.name)
            self.assertEqual(endpoint_group_ref['filters'],
                             endpoint_group.filters)

            # There is no guarantee description is present in endpoint groups
            if hasattr(endpoint_group_ref, 'description'):
                self.assertEqual(endpoint_group_ref['description'],
                                 endpoint_group.description)
        else:
            # Only check remaining mandatory attributes
            self.assertIsNotNone(endpoint_group.name)
            self.assertIsNotNone(endpoint_group.filters)


class EndpointGroupsTestCase(base.V3ClientTestCase, EndpointGroupsTestMixin):

    def test_create_endpoint_group(self):
        endpoint_group_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'filters': {'interface': 'internal'},
            'description': uuid.uuid4().hex}
        endpoint_group = self.client.endpoint_groups.create(
            **endpoint_group_ref)

        self.addCleanup(self.client.endpoint_groups.delete, endpoint_group)
        self.check_endpoint_group(endpoint_group, endpoint_group_ref)

    def test_get_endpoint_group(self):
        endpoint_group = fixtures.EndpointGroup(self.client)
        self.useFixture(endpoint_group)

        endpoint_ret = self.client.endpoint_groups.get(endpoint_group.id)
        self.check_endpoint_group(endpoint_ret, endpoint_group.ref)

        self.assertRaises(http.NotFound,
                          self.client.endpoint_groups.get,
                          uuid.uuid4().hex)

    def test_check_endpoint_group(self):
        endpoint_group = fixtures.EndpointGroup(self.client)
        self.useFixture(endpoint_group)

        self.client.endpoint_groups.check(endpoint_group.id)
        self.assertRaises(http.NotFound,
                          self.client.endpoint_groups.check,
                          uuid.uuid4().hex)

    def test_list_endpoint_groups(self):
        endpoint_group_one = fixtures.EndpointGroup(self.client)
        self.useFixture(endpoint_group_one)

        endpoint_group_two = fixtures.EndpointGroup(self.client)
        self.useFixture(endpoint_group_two)

        endpoint_groups = self.client.endpoint_groups.list()

        # All endpoints are valid
        for endpoint_group in endpoint_groups:
            self.check_endpoint_group(endpoint_group)

        self.assertIn(endpoint_group_one.entity, endpoint_groups)
        self.assertIn(endpoint_group_two.entity, endpoint_groups)

    def test_update_endpoint_group(self):
        endpoint_group = fixtures.EndpointGroup(self.client)
        self.useFixture(endpoint_group)

        new_name = fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex
        new_filters = {'interface': 'public'}
        new_description = uuid.uuid4().hex

        endpoint_group_ret = self.client.endpoint_groups.update(
            endpoint_group,
            name=new_name,
            filters=new_filters,
            description=new_description)

        endpoint_group.ref.update({'name': new_name, 'filters': new_filters,
                                   'description': new_description})
        self.check_endpoint_group(endpoint_group_ret, endpoint_group.ref)

    def test_delete_endpoint_group(self):
        endpoint_group = self.client.endpoint_groups.create(
            name=fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            filters={'interface': 'admin'},
            description=uuid.uuid4().hex)

        self.client.endpoint_groups.delete(endpoint_group.id)
        self.assertRaises(http.NotFound,
                          self.client.endpoint_groups.check,
                          endpoint_group.id)
        self.assertRaises(http.NotFound,
                          self.client.endpoint_groups.get,
                          endpoint_group.id)
