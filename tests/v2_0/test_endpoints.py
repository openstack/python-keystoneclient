import urlparse
import json

import httplib2

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

        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
        })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/endpoints'),
                              'POST',
                              body=json.dumps(req_body),
                              headers=self.TEST_POST_HEADERS) \
            .AndReturn((resp, resp['body']))
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
        resp = httplib2.Response({
            "status": 200,
            "body": "",
        })
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/endpoints/8f953'),
                              'DELETE',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.client.endpoints.delete('8f953')

    def test_list(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_ENDPOINTS),
        })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/endpoints'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        endpoint_list = self.client.endpoints.list()
        [self.assertTrue(isinstance(r, endpoints.Endpoint))
         for r in endpoint_list]
