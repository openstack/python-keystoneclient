import httplib2
import json

from keystoneclient.v2_0 import client
from keystoneclient import exceptions
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


class AuthenticateAgainstKeystoneTests(utils.TestCase):
    def setUp(self):
        super(AuthenticateAgainstKeystoneTests, self).setUp()
        self.TEST_RESPONSE_DICT = {
            "access": {
                "token": {
                    "expires": "12345",
                    "id": self.TEST_TOKEN,
                    "tenant": {
                        "id": self.TEST_TENANT_ID
                        },
                    },
                "user": {
                    "id": self.TEST_USER
                    },
                "serviceCatalog": self.TEST_SERVICE_CATALOG,
                },
            }
        self.TEST_REQUEST_BODY = {
            "auth": {
                "passwordCredentials": {
                    "username": self.TEST_USER,
                    "password": self.TEST_TOKEN,
                    },
                "tenantId": self.TEST_TENANT_ID,
                },
            }
        self.TEST_REQUEST_HEADERS = {
            'Content-Type': 'application/json',
            'User-Agent': 'python-keystoneclient',
            }

    def test_authenticate_failure(self):
        _auth = 'auth'
        _cred = 'passwordCredentials'
        _pass = 'password'
        self.TEST_REQUEST_BODY[_auth][_cred][_pass] = 'bad_key'
        resp = httplib2.Response({
            "status": 401,
            "body": json.dumps({
                "unauthorized": {
                    "message": "Unauthorized",
                    "code": "401",
                    },
                }),
            })

        # Implicit retry on API calls, so it gets called twice
        httplib2.Http.request(self.TEST_URL + "/tokens",
                              'POST',
                              body=json.dumps(self.TEST_REQUEST_BODY),
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        httplib2.Http.request(self.TEST_URL + "/tokens",
                              'POST',
                              body=json.dumps(self.TEST_REQUEST_BODY),
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        # Workaround for issue with assertRaises on python2.6
        # where with assertRaises(exceptions.Unauthorized): doesn't work
        # right
        def client_create_wrapper():
            client.Client(username=self.TEST_USER,
                          password="bad_key",
                          tenant_id=self.TEST_TENANT_ID,
                          auth_url=self.TEST_URL)

        self.assertRaises(exceptions.Unauthorized, client_create_wrapper)

    def test_auth_redirect(self):
        correct_response = json.dumps(self.TEST_RESPONSE_DICT)
        dict_responses = [
            {
                "headers": {
                    'location': self.TEST_ADMIN_URL + "/tokens",
                    },
                "status": 305,
                "body": "Use proxy",
                },
            {
                "headers": {},
                "status": 200,
                "body": correct_response,
                },
            ]
        responses = [(to_http_response(resp), resp['body'])
                     for resp in dict_responses]

        httplib2.Http.request(self.TEST_URL + "/tokens",
                              'POST',
                              body=json.dumps(self.TEST_REQUEST_BODY),
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn(responses[0])
        httplib2.Http.request(self.TEST_ADMIN_URL + "/tokens",
                              'POST',
                              body=json.dumps(self.TEST_REQUEST_BODY),
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn(responses[1])
        self.mox.ReplayAll()

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)

        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                             ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])

    def test_authenticate_success_password_scoped(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_RESPONSE_DICT),
            })

        httplib2.Http.request(self.TEST_URL + "/tokens",
                              'POST',
                              body=json.dumps(self.TEST_REQUEST_BODY),
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                             ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])

    def test_authenticate_success_password_unscoped(self):
        del self.TEST_RESPONSE_DICT['access']['serviceCatalog']
        del self.TEST_REQUEST_BODY['auth']['tenantId']
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_RESPONSE_DICT),
            })

        httplib2.Http.request(self.TEST_URL + "/tokens",
                              'POST',
                              body=json.dumps(self.TEST_REQUEST_BODY),
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertFalse('serviceCatalog' in cs.service_catalog.catalog)

    def test_authenticate_success_token_scoped(self):
        del self.TEST_REQUEST_BODY['auth']['passwordCredentials']
        self.TEST_REQUEST_BODY['auth']['token'] = {'id': self.TEST_TOKEN}
        self.TEST_REQUEST_HEADERS['X-Auth-Token'] = self.TEST_TOKEN
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_RESPONSE_DICT),
            })

        httplib2.Http.request(self.TEST_URL + "/tokens",
                              'POST',
                              body=json.dumps(self.TEST_REQUEST_BODY),
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        cs = client.Client(token=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                             ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])

    def test_authenticate_success_token_unscoped(self):
        del self.TEST_REQUEST_BODY['auth']['passwordCredentials']
        del self.TEST_REQUEST_BODY['auth']['tenantId']
        del self.TEST_RESPONSE_DICT['access']['serviceCatalog']
        self.TEST_REQUEST_BODY['auth']['token'] = {'id': self.TEST_TOKEN}
        self.TEST_REQUEST_HEADERS['X-Auth-Token'] = self.TEST_TOKEN
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_RESPONSE_DICT),
            })

        httplib2.Http.request(self.TEST_URL + "/tokens",
                              'POST',
                              body=json.dumps(self.TEST_REQUEST_BODY),
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        cs = client.Client(token=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertFalse('serviceCatalog' in cs.service_catalog.catalog)
