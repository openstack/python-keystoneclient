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

import copy
import json
import urlparse

import requests

from keystoneclient.v2_0 import endpoints
from tests import utils


class EndpointTests(utils.TestCase):
    def setUp(self):
        super(EndpointTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
        }
        self.TEST_POST_HEADERS = {
            'Content-Type': 'application/json',
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
        }
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

        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        requests.request('POST',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/endpoints'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        endpoint = self.client.endpoints.create(
            region=req_body['endpoint']['region'],
            publicurl=req_body['endpoint']['publicurl'],
            adminurl=req_body['endpoint']['adminurl'],
            internalurl=req_body['endpoint']['internalurl'],
            service_id=req_body['endpoint']['service_id']
        )
        self.assertTrue(isinstance(endpoint, endpoints.Endpoint))

    def test_delete(self):
        resp = utils.TestResponse({
            "status_code": 204,
            "text": "",
        })
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('DELETE',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/endpoints/8f953'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.endpoints.delete('8f953')

    def test_list(self):
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_ENDPOINTS),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/endpoints'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        endpoint_list = self.client.endpoints.list()
        [self.assertTrue(isinstance(r, endpoints.Endpoint))
         for r in endpoint_list]
