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

import uuid

from oslo_config import fixture as config
from six.moves import urllib
import testtools

from keystoneclient.auth import conf
from keystoneclient.contrib.auth.v3 import oidc
from keystoneclient import session
from keystoneclient.tests.unit.v3 import utils


ACCESS_TOKEN_ENDPOINT_RESP = {"access_token": "z5H1ITZLlJVDHQXqJun",
                              "token_type": "bearer",
                              "expires_in": 3599,
                              "scope": "profile",
                              "refresh_token": "DCERsh83IAhu9bhavrp"}

KEYSTONE_TOKEN_VALUE = uuid.uuid4().hex
UNSCOPED_TOKEN = {
    "token": {
        "issued_at": "2014-06-09T09:48:59.643406Z",
        "extras": {},
        "methods": ["oidc"],
        "expires_at": "2014-06-09T10:48:59.643375Z",
        "user": {
            "OS-FEDERATION": {
                "identity_provider": {
                    "id": "bluepages"
                },
                "protocol": {
                    "id": "oidc"
                },
                "groups": [
                    {"id": "1764fa5cf69a49a4918131de5ce4af9a"}
                ]
            },
            "id": "oidc_user%40example.com",
            "name": "oidc_user@example.com"
        }
    }
}


class AuthenticateOIDCTests(utils.TestCase):

    GROUP = 'auth'

    def setUp(self):
        super(AuthenticateOIDCTests, self).setUp()

        self.deprecations.expect_deprecations()

        self.conf_fixture = self.useFixture(config.Config())
        conf.register_conf_options(self.conf_fixture.conf, group=self.GROUP)

        self.session = session.Session()

        self.IDENTITY_PROVIDER = 'bluepages'
        self.PROTOCOL = 'oidc'
        self.USER_NAME = 'oidc_user@example.com'
        self.PASSWORD = uuid.uuid4().hex
        self.CLIENT_ID = uuid.uuid4().hex
        self.CLIENT_SECRET = uuid.uuid4().hex
        self.ACCESS_TOKEN_ENDPOINT = 'https://localhost:8020/oidc/token'
        self.FEDERATION_AUTH_URL = '%s/%s' % (
            self.TEST_URL,
            'OS-FEDERATION/identity_providers/bluepages/protocols/oidc/auth')

        self.oidcplugin = oidc.OidcPassword(
            self.TEST_URL,
            self.IDENTITY_PROVIDER,
            self.PROTOCOL,
            username=self.USER_NAME,
            password=self.PASSWORD,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            access_token_endpoint=self.ACCESS_TOKEN_ENDPOINT)

    @testtools.skip("TypeError: __init__() got an unexpected keyword"
                    " argument 'project_name'")
    def test_conf_params(self):
        """Ensure OpenID Connect config options work."""
        section = uuid.uuid4().hex
        identity_provider = uuid.uuid4().hex
        protocol = uuid.uuid4().hex
        username = uuid.uuid4().hex
        password = uuid.uuid4().hex
        client_id = uuid.uuid4().hex
        client_secret = uuid.uuid4().hex
        access_token_endpoint = uuid.uuid4().hex

        self.conf_fixture.config(auth_section=section, group=self.GROUP)
        conf.register_conf_options(self.conf_fixture.conf, group=self.GROUP)

        self.conf_fixture.register_opts(oidc.OidcPassword.get_options(),
                                        group=section)
        self.conf_fixture.config(auth_plugin='v3oidcpassword',
                                 identity_provider=identity_provider,
                                 protocol=protocol,
                                 username=username,
                                 password=password,
                                 client_id=client_id,
                                 client_secret=client_secret,
                                 access_token_endpoint=access_token_endpoint,
                                 group=section)

        a = conf.load_from_conf_options(self.conf_fixture.conf, self.GROUP)
        self.assertEqual(identity_provider, a.identity_provider)
        self.assertEqual(protocol, a.protocol)
        self.assertEqual(username, a.username)
        self.assertEqual(password, a.password)
        self.assertEqual(client_id, a.client_id)
        self.assertEqual(client_secret, a.client_secret)
        self.assertEqual(access_token_endpoint, a.access_token_endpoint)

    def test_initial_call_to_get_access_token(self):
        """Test initial call, expect JSON access token."""
        # Mock the output that creates the access token
        self.requests_mock.post(
            self.ACCESS_TOKEN_ENDPOINT,
            json=ACCESS_TOKEN_ENDPOINT_RESP)

        # Prep all the values and send the request
        grant_type = 'password'
        scope = 'profile email'
        client_auth = (self.CLIENT_ID, self.CLIENT_SECRET)
        payload = {'grant_type': grant_type, 'username': self.USER_NAME,
                   'password': self.PASSWORD, 'scope': scope}
        res = self.oidcplugin._get_access_token(self.session,
                                                client_auth,
                                                payload,
                                                self.ACCESS_TOKEN_ENDPOINT)

        # Verify the request matches the expected structure
        self.assertEqual(self.ACCESS_TOKEN_ENDPOINT, res.request.url)
        self.assertEqual('POST', res.request.method)
        encoded_payload = urllib.parse.urlencode(payload)
        self.assertEqual(encoded_payload, res.request.body)

    def test_second_call_to_protected_url(self):
        """Test subsequent call, expect Keystone token."""
        # Mock the output that creates the keystone token
        self.requests_mock.post(
            self.FEDERATION_AUTH_URL,
            json=UNSCOPED_TOKEN,
            headers={'X-Subject-Token': KEYSTONE_TOKEN_VALUE})

        # Prep all the values and send the request
        access_token = uuid.uuid4().hex
        headers = {'Authorization': 'Bearer ' + access_token}
        res = self.oidcplugin._get_keystone_token(self.session,
                                                  headers,
                                                  self.FEDERATION_AUTH_URL)

        # Verify the request matches the expected structure
        self.assertEqual(self.FEDERATION_AUTH_URL, res.request.url)
        self.assertEqual('POST', res.request.method)
        self.assertEqual(headers['Authorization'],
                         res.request.headers['Authorization'])

    def test_end_to_end_workflow(self):
        """Test full OpenID Connect workflow."""
        # Mock the output that creates the access token
        self.requests_mock.post(
            self.ACCESS_TOKEN_ENDPOINT,
            json=ACCESS_TOKEN_ENDPOINT_RESP)

        # Mock the output that creates the keystone token
        self.requests_mock.post(
            self.FEDERATION_AUTH_URL,
            json=UNSCOPED_TOKEN,
            headers={'X-Subject-Token': KEYSTONE_TOKEN_VALUE})

        response = self.oidcplugin.get_unscoped_auth_ref(self.session)
        self.assertEqual(KEYSTONE_TOKEN_VALUE, response.auth_token)
