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

from keystoneclient.v2_0 import services
from tests.v2_0 import utils


class ServiceTests(utils.TestCase):
    def setUp(self):
        super(ServiceTests, self).setUp()
        self.TEST_SERVICES = {
            "OS-KSADM:services": {
                "values": [
                    {
                        "name": "nova",
                        "type": "compute",
                        "description": "Nova-compatible service.",
                        "id": 1
                    },
                    {
                        "name": "keystone",
                        "type": "identity",
                        "description": "Keystone-compatible service.",
                        "id": 2
                    },
                ],
            },
        }

    @httpretty.activate
    def test_create(self):
        req_body = {
            "OS-KSADM:service": {
                "name": "swift",
                "type": "object-store",
                "description": "Swift-compatible service.",
            }
        }
        resp_body = {
            "OS-KSADM:service": {
                "name": "swift",
                "type": "object-store",
                "description": "Swift-compatible service.",
                "id": 3,
            }
        }
        self.stub_url(httpretty.POST, ['OS-KSADM', 'services'], json=resp_body)

        service = self.client.services.create(
            req_body['OS-KSADM:service']['name'],
            req_body['OS-KSADM:service']['type'],
            req_body['OS-KSADM:service']['description'])
        self.assertTrue(isinstance(service, services.Service))
        self.assertEqual(service.id, 3)
        self.assertEqual(service.name, req_body['OS-KSADM:service']['name'])
        self.assertRequestBodyIs(json=req_body)

    @httpretty.activate
    def test_delete(self):
        self.stub_url(httpretty.DELETE, ['OS-KSADM', 'services', '1'],
                      status=204)

        self.client.services.delete(1)

    @httpretty.activate
    def test_get(self):
        test_services = self.TEST_SERVICES['OS-KSADM:services']['values'][0]

        self.stub_url(httpretty.GET, ['OS-KSADM', 'services', '1'],
                      json={'OS-KSADM:service': test_services})

        service = self.client.services.get(1)
        self.assertTrue(isinstance(service, services.Service))
        self.assertEqual(service.id, 1)
        self.assertEqual(service.name, 'nova')
        self.assertEqual(service.type, 'compute')

    @httpretty.activate
    def test_list(self):
        self.stub_url(httpretty.GET, ['OS-KSADM', 'services'],
                      json=self.TEST_SERVICES)

        service_list = self.client.services.list()
        [self.assertTrue(isinstance(r, services.Service))
         for r in service_list]
