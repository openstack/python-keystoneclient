# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import httpretty

from keystoneclient.v2_0 import endpoints
from tests.v2_0 import utils


class EndpointTests(utils.TestCase):
    def setUp(self):
        super(EndpointTests, self).setUp()
        self.TEST_ENDPOINTS = {
            'endpoints': [
                {
                    'adminurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'id': '8f9531231e044e218824b0e58688d262',
                    'internalurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'publicurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'region': 'RegionOne',
                },
                {
                    'adminurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'id': '8f9531231e044e218824b0e58688d263',
                    'internalurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'publicurl': 'http://host-1:8774/v1.1/$(tenant_id)s',
                    'region': 'RegionOne',
                }
            ]
        }

    @httpretty.activate
    def test_create(self):
        req_body = {
            "endpoint": {
                "region": "RegionOne",
                "publicurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "internalurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "adminurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "service_id": "e044e21",
            }
        }

        resp_body = {
            "endpoint": {
                "adminurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "region": "RegionOne",
                "id": "1fd485b2ffd54f409a5ecd42cba11401",
                "internalurl": "http://host-3:8774/v1.1/$(tenant_id)s",
                "publicurl": "http://host-3:8774/v1.1/$(tenant_id)s",
            }
        }

        self.stub_url(httpretty.POST, ['endpoints'], json=resp_body)

        endpoint = self.client.endpoints.create(
            region=req_body['endpoint']['region'],
            publicurl=req_body['endpoint']['publicurl'],
            adminurl=req_body['endpoint']['adminurl'],
            internalurl=req_body['endpoint']['internalurl'],
            service_id=req_body['endpoint']['service_id']
        )
        self.assertTrue(isinstance(endpoint, endpoints.Endpoint))
        self.assertRequestBodyIs(json=req_body)

    @httpretty.activate
    def test_delete(self):
        self.stub_url(httpretty.DELETE, ['endpoints', '8f953'], status=204)
        self.client.endpoints.delete('8f953')

    @httpretty.activate
    def test_list(self):
        self.stub_url(httpretty.GET, ['endpoints'], json=self.TEST_ENDPOINTS)

        endpoint_list = self.client.endpoints.list()
        [self.assertTrue(isinstance(r, endpoints.Endpoint))
         for r in endpoint_list]
