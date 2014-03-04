# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid

import httpretty
import oauthlib.oauth1 as oauth1

from keystoneclient.auth.identity import v3
from keystoneclient import session
from keystoneclient.tests.v3 import client_fixtures
from keystoneclient.tests.v3 import utils
from keystoneclient.v3.contrib.oauth1 import access_tokens
from keystoneclient.v3.contrib.oauth1 import consumers
from keystoneclient.v3.contrib.oauth1 import request_tokens


class ConsumerTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(ConsumerTests, self).setUp()
        self.key = 'consumer'
        self.collection_key = 'consumers'
        self.model = consumers.Consumer
        self.manager = self.client.oauth1.consumers
        self.path_prefix = 'OS-OAUTH1'

    def new_ref(self, **kwargs):
        kwargs = super(ConsumerTests, self).new_ref(**kwargs)
        kwargs.setdefault('description', uuid.uuid4().hex)
        return kwargs

    @httpretty.activate
    def test_description_is_optional(self, **kwargs):
        consumer_id = uuid.uuid4().hex
        resp_ref = {'consumer': {'description': None,
                                 'id': consumer_id}}

        self.stub_url(httpretty.POST,
                      [self.path_prefix, self.collection_key],
                      status=200, json=resp_ref)

        consumer = self.manager.create()
        self.assertIsNone(consumer.description)


class TokenTests(utils.TestCase):
    def _new_oauth_token(self):
        key = uuid.uuid4().hex
        secret = uuid.uuid4().hex
        token = 'oauth_token=%s&oauth_token_secret=%s' % (key, secret)
        return (key, secret, token)

    def _new_oauth_token_with_expires_at(self):
        key = uuid.uuid4().hex
        secret = uuid.uuid4().hex
        expires_at = uuid.uuid4().hex
        token = ('oauth_token=%s&oauth_token_secret=%s'
                 '&oauth_expires_at=%s' % (key, secret, expires_at))
        return (key, secret, expires_at, token)

    def _validate_oauth_headers(self, auth_header, oc):
        self.assertTrue(auth_header.startswith('OAuth '))
        auth_header = auth_header[6:]
        header_params = oc.get_oauth_params()
        parameters = dict(header_params)

        self.assertEqual(parameters['oauth_signature_method'], 'HMAC-SHA1')
        self.assertEqual(parameters['oauth_version'], '1.0')
        self.assertIsNotNone(parameters['oauth_nonce'])
        self.assertIsNotNone(parameters['oauth_timestamp'])
        self.assertEqual(parameters['oauth_consumer_key'], oc.client_key)
        if oc.resource_owner_key:
            self.assertEqual(parameters['oauth_token'], oc.resource_owner_key)
        if oc.verifier:
            self.assertEqual(parameters['oauth_verifier'], oc.verifier)
        return parameters


class RequestTokenTests(TokenTests):
    def setUp(self):
        super(RequestTokenTests, self).setUp()
        self.model = request_tokens.RequestToken
        self.manager = self.client.oauth1.request_tokens
        self.path_prefix = 'OS-OAUTH1'

    @httpretty.activate
    def test_authorize_request_token(self):
        request_key = uuid.uuid4().hex
        verifier = uuid.uuid4().hex
        resp_ref = {'token': {'oauth_verifier': verifier}}
        role_ids = uuid.uuid4().hex
        exp_body = {'roles': [{'id': role_ids}]}

        self.stub_url(httpretty.PUT,
                      [self.path_prefix, 'authorize', request_key],
                      status=200, json=resp_ref)

        # Assert the manager is returning the expected data
        token = self.manager.authorize(request_key, [role_ids])
        self.assertEqual(token.oauth_verifier, verifier)

        # Assert that the request was sent in the expected structure
        self.assertRequestBodyIs(json=exp_body)

    @httpretty.activate
    def test_create_request_token(self):
        project_id = uuid.uuid4().hex
        consumer_key = uuid.uuid4().hex
        consumer_secret = uuid.uuid4().hex

        request_key, request_secret, resp_ref = self._new_oauth_token()
        self.stub_url(httpretty.POST, [self.path_prefix, 'request_token'],
                      status=201, json=resp_ref)

        # Assert the manager is returning request token object
        request_token = self.manager.create(consumer_key, consumer_secret,
                                            project_id)
        self.assertIsInstance(request_token, self.model)
        self.assertEqual(request_token.request_key, request_key)
        self.assertEqual(request_token.request_secret, request_secret)

        # Assert that the project id is in the header
        self.assertRequestHeaderEqual('requested_project_id', project_id)
        req_headers = httpretty.last_request().headers

        # Assert that the headers have the same oauthlib data
        oc = oauth1.Client(consumer_key, client_secret=consumer_secret,
                           signature_method=oauth1.SIGNATURE_HMAC,
                           callback_uri="oob")
        self._validate_oauth_headers(req_headers['Authorization'], oc)


class AccessTokenTests(TokenTests):
    def setUp(self):
        super(AccessTokenTests, self).setUp()
        self.manager = self.client.oauth1.access_tokens
        self.model = access_tokens.AccessToken
        self.path_prefix = 'OS-OAUTH1'

    @httpretty.activate
    def test_create_access_token_expires_at(self):
        verifier = uuid.uuid4().hex
        consumer_key = uuid.uuid4().hex
        consumer_secret = uuid.uuid4().hex
        request_key = uuid.uuid4().hex
        request_secret = uuid.uuid4().hex

        t = self._new_oauth_token_with_expires_at()
        access_key, access_secret, expires_at, resp_ref = t
        self.stub_url(httpretty.POST, [self.path_prefix, 'access_token'],
                      status=201, json=resp_ref)

        # Assert that the manager creates an access token object
        access_token = self.manager.create(consumer_key, consumer_secret,
                                           request_key, request_secret,
                                           verifier)
        self.assertIsInstance(access_token, self.model)
        self.assertEqual(access_token.access_key, access_key)
        self.assertEqual(access_token.access_secret, access_secret)
        self.assertEqual(access_token.expires, expires_at)

        # Assert that the headers have the same oauthlib data
        req_headers = httpretty.last_request().headers
        oc = oauth1.Client(consumer_key, client_secret=consumer_secret,
                           resource_owner_key=request_key,
                           resource_owner_secret=request_secret,
                           signature_method=oauth1.SIGNATURE_HMAC,
                           verifier=verifier)
        self._validate_oauth_headers(req_headers['Authorization'], oc)


class AuthenticateWithOAuthTests(TokenTests):
    def setUp(self):
        super(AuthenticateWithOAuthTests, self).setUp()

    @httpretty.activate
    def test_oauth_authenticate_success(self):
        TEST_TOKEN = "abcdef"
        consumer_key = uuid.uuid4().hex
        consumer_secret = uuid.uuid4().hex
        access_key = uuid.uuid4().hex
        access_secret = uuid.uuid4().hex

        # Just use an existing project scoped token and change
        # the methods to oauth1, and add an OS-OAUTH1 section.
        oauth_token = client_fixtures.PROJECT_SCOPED_TOKEN
        oauth_token['methods'] = ["oauth1"]
        oauth_token['OS-OAUTH1'] = {"consumer_id": consumer_key,
                                    "access_token_id": access_key}
        self.stub_auth(json=oauth_token, subject_token=TEST_TOKEN)

        a = v3.OAuth(self.TEST_URL, consumer_key=consumer_key,
                     consumer_secret=consumer_secret,
                     access_key=access_key,
                     access_secret=access_secret)
        s = session.Session(auth=a)
        t = s.get_token()

        self.assertEqual(t, TEST_TOKEN)

        OAUTH_REQUEST_BODY = {
            "auth": {
                "identity": {
                    "methods": ["oauth1"],
                    "oauth1": {}
                }
            }
        }

        self.assertRequestBodyIs(json=OAUTH_REQUEST_BODY)

        # Assert that the headers have the same oauthlib data
        req_headers = httpretty.last_request().headers
        oc = oauth1.Client(consumer_key, client_secret=consumer_secret,
                           resource_owner_key=access_key,
                           resource_owner_secret=access_secret,
                           signature_method=oauth1.SIGNATURE_HMAC)
        self._validate_oauth_headers(req_headers['Authorization'], oc)
