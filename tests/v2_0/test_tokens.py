#import urlparse
#import json

#import httplib2

#from keystoneclient.v2_0 import tokens
from tests import utils


class TokenTests(utils.TestCase):
    def setUp(self):
        #super(ServiceTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {'X-Auth-Token': 'aToken',
                                     'User-Agent': 'python-keystoneclient'}
        self.TEST_POST_HEADERS = {'Content-Type': 'application/json',
                                  'X-Auth-Token': 'aToken',
                                  'User-Agent': 'python-keystoneclient'}
'''
    def test_create(self):
        req_body = {"OS-KSADM:service": {"name": "swift",
                                "type": "object-store",
                                "description": "Swift-compatible service."}}
        resp_body = {"OS-KSADM:service": {"name": "swift",
                                "type": "object-store",
                                "description": "Swift-compatible service.",
                                "id": 3}}
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/OS-KSADM/services'),
                              'POST',
                              body=json.dumps(req_body),
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        service = self.client.services.create(
                    req_body['OS-KSADM:service']['name'],
                    req_body['OS-KSADM:service']['type'],
                    req_body['OS-KSADM:service']['description'])
        self.assertTrue(isinstance(service, services.Service))
        self.assertEqual(service.id, 3)
        self.assertEqual(service.name, req_body['OS-KSADM:service']['name'])
'''
