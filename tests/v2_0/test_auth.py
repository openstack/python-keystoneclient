import copy
from datetime import timedelta
import json

import requests

from keystoneclient.v2_0 import client
from keystoneclient import exceptions
from keystoneclient.openstack.common import timeutils
from tests import utils


class AuthenticateAgainstKeystoneTests(utils.TestCase):
    def setUp(self):
        super(AuthenticateAgainstKeystoneTests, self).setUp()
        self.TEST_RESPONSE_DICT = {
            "access": {
                "token": {
                    "expires": "2999-01-01T00:00:10Z",
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

    def test_authenticate_success_expired(self):
        # Build an expired token
        self.TEST_RESPONSE_DICT['access']['token']['expires'] = \
            (timeutils.utcnow() - timedelta(1)).isoformat()
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY)
        requests.request('POST',
                         self.TEST_URL + "/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        cs = client.Client(tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL,
                           username=self.TEST_USER,
                           password=self.TEST_TOKEN)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])

        # Build a new response
        self.mox.ResetAll()
        TEST_TOKEN = "abcdef"
        self.TEST_RESPONSE_DICT['access']['token']['expires'] = \
            "2999-01-01T00:00:10Z"
        self.TEST_RESPONSE_DICT['access']['token']['id'] = TEST_TOKEN

        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
        })
        requests.request('POST',
                         self.TEST_URL + "/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.assertEqual(cs.auth_token, TEST_TOKEN)

    def test_authenticate_failure(self):
        _auth = 'auth'
        _cred = 'passwordCredentials'
        _pass = 'password'
        self.TEST_REQUEST_BODY[_auth][_cred][_pass] = 'bad_key'
        resp = utils.TestResponse({
            "status_code": 401,
            "text": json.dumps({
                "unauthorized": {
                    "message": "Unauthorized",
                    "code": "401",
                },
            }),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY)
        requests.request('POST',
                         self.TEST_URL + "/tokens",
                         **kwargs).AndReturn((resp))
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
                "status_code": 305,
                "text": "Use proxy",
            },
            {
                "headers": {},
                "status_code": 200,
                "text": correct_response,
            },
        ]
        responses = [(utils.TestResponse(resp))
                     for resp in dict_responses]

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY)
        requests.request('POST',
                         self.TEST_URL + "/tokens",
                         **kwargs).AndReturn(responses[0])
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY)
        requests.request('POST',
                         self.TEST_ADMIN_URL + "/tokens",
                         **kwargs).AndReturn(responses[1])
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
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY)
        requests.request('POST',
                         self.TEST_URL + "/tokens",
                         **kwargs).AndReturn((resp))
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
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY)
        requests.request('POST',
                         self.TEST_URL + "/tokens",
                         **kwargs).AndReturn((resp))
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
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY)
        requests.request('POST',
                         self.TEST_URL + "/tokens",
                         **kwargs).AndReturn((resp))
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
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_RESPONSE_DICT),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        kwargs['data'] = json.dumps(self.TEST_REQUEST_BODY)
        requests.request('POST',
                         self.TEST_URL + "/tokens",
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        cs = client.Client(token=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertFalse('serviceCatalog' in cs.service_catalog.catalog)
