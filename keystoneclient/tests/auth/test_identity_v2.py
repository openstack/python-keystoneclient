# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import httpretty

from keystoneclient.auth.identity import v2
from keystoneclient import exceptions
from keystoneclient import session
from keystoneclient.tests import utils


class V2IdentityPlugin(utils.TestCase):

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v2.0')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v2.0')

    TEST_PASS = 'password'

    TEST_SERVICE_CATALOG = []

    def setUp(self):
        super(V2IdentityPlugin, self).setUp()
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

    def stub_auth(self, **kwargs):
        self.stub_url(httpretty.POST, ['tokens'], **kwargs)

    @httpretty.activate
    def test_authenticate_with_username_password(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS)
        s = session.Session(a)
        s.get_token()

        req = {'auth': {'passwordCredentials': {'username': self.TEST_USER,
                                                'password': self.TEST_PASS}}}
        self.assertRequestBodyIs(json=req)
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    @httpretty.activate
    def test_authenticate_with_username_password_scoped(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS, tenant_id=self.TEST_TENANT_ID)
        s = session.Session(a)
        s.get_token()

        req = {'auth': {'passwordCredentials': {'username': self.TEST_USER,
                                                'password': self.TEST_PASS},
                        'tenantId': self.TEST_TENANT_ID}}
        self.assertRequestBodyIs(json=req)
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    @httpretty.activate
    def test_authenticate_with_token(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Token(self.TEST_URL, 'foo')
        s = session.Session(a)
        s.get_token()

        req = {'auth': {'token': {'id': 'foo'}}}
        self.assertRequestBodyIs(json=req)
        self.assertRequestHeaderEqual('x-Auth-Token', 'foo')
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)

    def test_missing_auth_params(self):
        self.assertRaises(exceptions.NoMatchingPlugin, v2.Auth._factory,
                          self.TEST_URL)

    @httpretty.activate
    def test_with_trust_id(self):
        self.stub_auth(json=self.TEST_RESPONSE_DICT)
        a = v2.Password(self.TEST_URL, username=self.TEST_USER,
                        password=self.TEST_PASS, trust_id='trust')
        s = session.Session(a)
        s.get_token()

        req = {'auth': {'passwordCredentials': {'username': self.TEST_USER,
                                                'password': self.TEST_PASS},
                        'trust_id': 'trust'}}

        self.assertRequestBodyIs(json=req)
        self.assertEqual(s.auth.auth_ref.auth_token, self.TEST_TOKEN)
