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


class RegionsTestCase(base.V3ClientTestCase):

    def check_region(self, region, region_ref=None):
        self.assertIsNotNone(region.id)
        self.assertIn('self', region.links)
        self.assertIn('/regions/' + region.id, region.links['self'])

        # There is no guarantee the below attributes are present in region
        if hasattr(region_ref, 'description'):
            self.assertEqual(region_ref['description'], region.description)
        if hasattr(region_ref, 'parent_region'):
            self.assertEqual(
                region_ref['parent_region'],
                region.parent_region)

    def test_create_region(self):
        region_ref = {'description': uuid.uuid4().hex}

        region = self.client.regions.create(**region_ref)
        self.addCleanup(self.client.regions.delete, region)
        self.check_region(region, region_ref)

    def test_get_region(self):
        region = fixtures.Region(self.client)
        self.useFixture(region)

        region_ret = self.client.regions.get(region.id)
        self.check_region(region_ret, region.ref)

    def test_list_regions(self):
        region_one = fixtures.Region(self.client)
        self.useFixture(region_one)

        region_two = fixtures.Region(self.client, parent_region=region_one.id)
        self.useFixture(region_two)

        regions = self.client.regions.list()

        # All regions are valid
        for region in regions:
            self.check_region(region)

        self.assertIn(region_one.entity, regions)
        self.assertIn(region_two.entity, regions)

    def test_update_region(self):
        parent = fixtures.Region(self.client)
        self.useFixture(parent)

        region = fixtures.Region(self.client)
        self.useFixture(region)

        new_description = uuid.uuid4().hex
        region_ret = self.client.regions.update(region.id,
                                                description=new_description,
                                                parent_region=parent.id)
        self.check_region(region_ret, region.ref)

    def test_delete_region(self):
        region = self.client.regions.create()

        self.client.regions.delete(region.id)
        self.assertRaises(http.NotFound,
                          self.client.regions.get,
                          region.id)
