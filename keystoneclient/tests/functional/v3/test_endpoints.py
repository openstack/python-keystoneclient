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


class EndpointsTestCase(base.V3ClientTestCase):

    def check_endpoint(self, endpoint, endpoint_ref=None):
        self.assertIsNotNone(endpoint.id)
        self.assertIn('self', endpoint.links)
        self.assertIn('/endpoints/' + endpoint.id, endpoint.links['self'])

        if endpoint_ref:
            self.assertEqual(endpoint_ref['service'], endpoint.service_id)
            self.assertEqual(endpoint_ref['url'], endpoint.url)
            self.assertEqual(endpoint_ref['interface'], endpoint.interface)
            self.assertEqual(endpoint_ref['enabled'], endpoint.enabled)

            # There is no guarantee below attributes are present in endpoint
            if hasattr(endpoint_ref, 'region'):
                self.assertEqual(endpoint_ref['region'], endpoint.region)

        else:
            # Only check remaining mandatory attributes
            self.assertIsNotNone(endpoint.service_id)
            self.assertIsNotNone(endpoint.url)
            self.assertIsNotNone(endpoint.interface)
            self.assertIsNotNone(endpoint.enabled)

    def test_create_endpoint(self):
        service = fixtures.Service(self.client)
        self.useFixture(service)

        endpoint_ref = {'service': service.id,
                        'url': 'http://' + uuid.uuid4().hex,
                        'enabled': True,
                        'interface': 'public'}
        endpoint = self.client.endpoints.create(**endpoint_ref)

        self.addCleanup(self.client.endpoints.delete, endpoint)
        self.check_endpoint(endpoint, endpoint_ref)

    def test_get_endpoint(self):
        service = fixtures.Service(self.client)
        self.useFixture(service)

        interfaces = ['public', 'admin', 'internal']
        for interface in interfaces:
            endpoint = fixtures.Endpoint(self.client, service.id, interface)
            self.useFixture(endpoint)
            endpoint_ret = self.client.endpoints.get(endpoint.id)
            # All endpoints are valid
            self.check_endpoint(endpoint_ret, endpoint.ref)

    def test_list_endpoints(self):
        service = fixtures.Service(self.client)
        self.useFixture(service)

        region = fixtures.Region(self.client)
        self.useFixture(region)

        endpoint_one = fixtures.Endpoint(self.client, service.id, 'public',
                                         region=region.id)
        self.useFixture(endpoint_one)

        endpoint_two = fixtures.Endpoint(self.client, service.id, 'admin',
                                         region=region.id)
        self.useFixture(endpoint_two)

        endpoint_three = fixtures.Endpoint(self.client, service.id, 'internal',
                                           region=region.id)
        self.useFixture(endpoint_three)

        endpoints = self.client.endpoints.list()

        # All endpoints are valid
        for endpoint in endpoints:
            self.check_endpoint(endpoint)

        self.assertIn(endpoint_one.entity, endpoints)
        self.assertIn(endpoint_two.entity, endpoints)
        self.assertIn(endpoint_three.entity, endpoints)

    def test_update_endpoint(self):
        service = fixtures.Service(self.client)
        self.useFixture(service)

        new_service = fixtures.Service(self.client)
        self.useFixture(new_service)

        new_region = fixtures.Region(self.client)
        self.useFixture(new_region)

        endpoint = fixtures.Endpoint(self.client, service.id, 'public')
        self.useFixture(endpoint)

        new_url = 'http://' + uuid.uuid4().hex
        new_interface = 'internal'
        new_enabled = False

        endpoint_ret = self.client.endpoints.update(endpoint.id,
                                                    service=new_service.id,
                                                    url=new_url,
                                                    interface=new_interface,
                                                    enabled=new_enabled,
                                                    region=new_region.id)

        endpoint.ref.update({'service': new_service.id, 'url': new_url,
                             'interface': new_interface,
                             'enabled': new_enabled,
                             'region': new_region.entity})
        self.check_endpoint(endpoint_ret, endpoint.ref)

    def test_delete_endpoint(self):
        service = fixtures.Service(self.client)
        self.useFixture(service)
        endpoint = self.client.endpoints.create(service=service.id,
                                                url='http://' +
                                                    uuid.uuid4().hex,
                                                enabled=True,
                                                interface='public')

        self.client.endpoints.delete(endpoint.id)
        self.assertRaises(http.NotFound,
                          self.client.endpoints.get,
                          endpoint.id)
