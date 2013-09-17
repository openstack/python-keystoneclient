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

import datetime
import json

import httpretty

from keystoneclient import exceptions
from keystoneclient.openstack.common import timeutils
from keystoneclient.v2_0 import client
from tests.v2_0 import utils


class AuthenticateAgainstKeystoneTests(utils.TestCase):
    def setUp(self):
        super(AuthenticateAgainstKeystoneTests, self).setUp()
        self.TEST_RESPONSE_DICT = {
            "access": {
                "token": {
                    "expires": "2020-01-01T00:00:10.000123Z",
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

    @httpretty.activate
    def test_authenticate_success_expired(self):
        # Build an expired token
        self.TEST_RESPONSE_DICT['access']['token']['expires'] = \
            (timeutils.utcnow() - datetime.timedelta(1)).isoformat()

        exp_resp = httpretty.Response(body=json.dumps(self.TEST_RESPONSE_DICT),
                                      content_type='application/json')

        # Build a new response
        TEST_TOKEN = "abcdef"
        self.TEST_RESPONSE_DICT['access']['token']['expires'] = \
            '2020-01-01T00:00:10.000123Z'
        self.TEST_RESPONSE_DICT['access']['token']['id'] = TEST_TOKEN

        new_resp = httpretty.Response(body=json.dumps(self.TEST_RESPONSE_DICT),
                                      content_type='application/json')

        # return expired first, and then the new response
        self.stub_auth(responses=[exp_resp, new_resp])

        cs = client.Client(tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL,
                           username=self.TEST_USER,
                           password=self.TEST_TOKEN)

        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])

        self.assertEqual(cs.auth_token, TEST_TOKEN)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    @httpretty.activate
    def test_authenticate_failure(self):
        _auth = 'auth'
        _cred = 'passwordCredentials'
        _pass = 'password'
        self.TEST_REQUEST_BODY[_auth][_cred][_pass] = 'bad_key'
        error = {"unauthorized": {"message": "Unauthorized",
                                  "code": "401"}}

        self.stub_auth(status=401, json=error)

        # Workaround for issue with assertRaises on python2.6
        # where with assertRaises(exceptions.Unauthorized): doesn't work
        # right
        def client_create_wrapper():
            client.Client(username=self.TEST_USER,
                          password="bad_key",
                          tenant_id=self.TEST_TENANT_ID,
                          auth_url=self.TEST_URL)

        self.assertRaises(exceptions.Unauthorized, client_create_wrapper)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    @httpretty.activate
    def test_auth_redirect(self):
        self.stub_auth(status=305, body='Use Proxy',
                       location=self.TEST_ADMIN_URL + "/tokens")

        self.stub_auth(base_url=self.TEST_ADMIN_URL,
                       json=self.TEST_RESPONSE_DICT)

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)

        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    @httpretty.activate
    def test_authenticate_success_password_scoped(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    @httpretty.activate
    def test_authenticate_success_password_unscoped(self):
        del self.TEST_RESPONSE_DICT['access']['serviceCatalog']
        del self.TEST_REQUEST_BODY['auth']['tenantId']

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(username=self.TEST_USER,
                           password=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertFalse('serviceCatalog' in cs.service_catalog.catalog)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    @httpretty.activate
    def test_authenticate_success_token_scoped(self):
        del self.TEST_REQUEST_BODY['auth']['passwordCredentials']
        self.TEST_REQUEST_BODY['auth']['token'] = {'id': self.TEST_TOKEN}
        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(token=self.TEST_TOKEN,
                           tenant_id=self.TEST_TENANT_ID,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.management_url,
                         self.TEST_RESPONSE_DICT["access"]["serviceCatalog"][3]
                         ['endpoints'][0]["adminURL"])
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)

    @httpretty.activate
    def test_authenticate_success_token_unscoped(self):
        del self.TEST_REQUEST_BODY['auth']['passwordCredentials']
        del self.TEST_REQUEST_BODY['auth']['tenantId']
        del self.TEST_RESPONSE_DICT['access']['serviceCatalog']
        self.TEST_REQUEST_BODY['auth']['token'] = {'id': self.TEST_TOKEN}

        self.stub_auth(json=self.TEST_RESPONSE_DICT)

        cs = client.Client(token=self.TEST_TOKEN,
                           auth_url=self.TEST_URL)
        self.assertEqual(cs.auth_token,
                         self.TEST_RESPONSE_DICT["access"]["token"]["id"])
        self.assertFalse('serviceCatalog' in cs.service_catalog.catalog)
        self.assertRequestBodyIs(json=self.TEST_REQUEST_BODY)
