import httplib2
import json

from keystoneclient.generic import client
from tests import utils


def to_http_response(resp_dict):
    """
    Utility function to convert a python dictionary
    (e.g. {'status':status, 'body': body, 'headers':headers}
    to an httplib2 response.
    """
    resp = httplib2.Response(resp_dict)
    for k, v in resp_dict['headers'].items():
        resp[k] = v
    return resp


class DiscoverKeystoneTests(utils.UnauthenticatedTestCase):
    def setUp(self):
        super(DiscoverKeystoneTests, self).setUp()
        self.TEST_RESPONSE_DICT = {
            "versions": {
                "values": [{
                    "id": "v2.0",
                    "status": "beta",
                    "updated": "2011-11-19T00:00:00Z",
                    "links": [
                        {"rel": "self",
                         "href": "http://127.0.0.1:5000/v2.0/",
                        },
                        {"rel": "describedby",
                         "type": "text/html",
                         "href": "http://docs.openstack.org/api/"
                         "openstack-identity-service/2.0/content/",
                        }, {
                            "rel": "describedby",
                            "type": "application/pdf",
                            "href": "http://docs.openstack.org/api/"
                                    "openstack-identity-service/2.0/"
                                    "identity-dev-guide-2.0.pdf",
                        }, {
                            "rel": "describedby",
                            "type": "application/vnd.sun.wadl+xml",
                            "href": "http://127.0.0.1:5000/v2.0/identity.wadl",
                        }],
                    "media-types": [{
                        "base": "application/xml",
                        "type": "application/vnd.openstack.identity-v2.0+xml",
                    },
                    {
                        "base": "application/json",
                        "type": "application/vnd.openstack.identity-v2.0+json",
                    }],
                }],
            },
        }
        self.TEST_REQUEST_HEADERS = {
            'User-Agent': 'python-keystoneclient',
            'Accept': 'application/json',
        }

    def test_get_versions(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_RESPONSE_DICT),
        })

        httplib2.Http.request(self.TEST_ROOT_URL,
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        cs = client.Client()
        versions = cs.discover(self.TEST_ROOT_URL)
        self.assertIsInstance(versions, dict)
        self.assertIn('message', versions)
        self.assertIn('v2.0', versions)
        self.assertEquals(
            versions['v2.0']['url'],
            self.TEST_RESPONSE_DICT['versions']['values'][0]['links'][0]
            ['href'])

    def test_get_version_local(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_RESPONSE_DICT),
        })

        httplib2.Http.request("http://localhost:35357",
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        cs = client.Client()
        versions = cs.discover()
        self.assertIsInstance(versions, dict)
        self.assertIn('message', versions)
        self.assertIn('v2.0', versions)
        self.assertEquals(
            versions['v2.0']['url'],
            self.TEST_RESPONSE_DICT['versions']['values'][0]['links'][0]
            ['href'])
