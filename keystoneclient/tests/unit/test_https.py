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

import requests
from unittest import mock

from keystoneclient import httpclient
from keystoneclient.tests.unit import utils


FAKE_RESPONSE = utils.test_response(json={'hi': 'there'})

REQUEST_URL = 'https://127.0.0.1:5000/hi'
RESPONSE_BODY = '{"hi": "there"}'


def get_client():
    cl = httpclient.HTTPClient(username="username", password="password",
                               project_id="tenant", auth_url="auth_test",
                               cacert="ca.pem", cert=('cert.pem', "key.pem"))
    return cl


def get_authed_client():
    cl = get_client()
    cl.management_url = "https://127.0.0.1:5000"
    cl.auth_token = "token"
    return cl


class ClientTest(utils.TestCase):

    @mock.patch.object(requests, 'request')
    def test_get(self, MOCK_REQUEST):
        MOCK_REQUEST.return_value = FAKE_RESPONSE
        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            cl = get_authed_client()

        with self.deprecations.expect_deprecations_here():
            resp, body = cl.get("/hi")

        # this may become too tightly couple later
        mock_args, mock_kwargs = MOCK_REQUEST.call_args

        self.assertEqual(mock_args[0], 'GET')
        self.assertEqual(mock_args[1], REQUEST_URL)
        self.assertEqual(mock_kwargs['headers']['X-Auth-Token'], 'token')
        self.assertEqual(mock_kwargs['cert'], ('cert.pem', 'key.pem'))
        self.assertEqual(mock_kwargs['verify'], 'ca.pem')

        # Automatic JSON parsing
        self.assertEqual(body, {"hi": "there"})

    @mock.patch.object(requests, 'request')
    def test_post(self, MOCK_REQUEST):
        MOCK_REQUEST.return_value = FAKE_RESPONSE
        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            cl = get_authed_client()

        with self.deprecations.expect_deprecations_here():
            cl.post("/hi", body=[1, 2, 3])

        # this may become too tightly couple later
        mock_args, mock_kwargs = MOCK_REQUEST.call_args

        self.assertEqual(mock_args[0], 'POST')
        self.assertEqual(mock_args[1], REQUEST_URL)
        self.assertEqual(mock_kwargs['data'], '[1, 2, 3]')
        self.assertEqual(mock_kwargs['headers']['X-Auth-Token'], 'token')
        self.assertEqual(mock_kwargs['cert'], ('cert.pem', 'key.pem'))
        self.assertEqual(mock_kwargs['verify'], 'ca.pem')

    @mock.patch.object(requests, 'request')
    def test_post_auth(self, MOCK_REQUEST):
        MOCK_REQUEST.return_value = FAKE_RESPONSE
        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            cl = httpclient.HTTPClient(
                username="username", password="password", project_id="tenant",
                auth_url="auth_test", cacert="ca.pem",
                cert=('cert.pem', 'key.pem'))
        cl.management_url = "https://127.0.0.1:5000"
        cl.auth_token = "token"
        with self.deprecations.expect_deprecations_here():
            cl.post("/hi", body=[1, 2, 3])

        # this may become too tightly couple later
        mock_args, mock_kwargs = MOCK_REQUEST.call_args

        self.assertEqual(mock_args[0], 'POST')
        self.assertEqual(mock_args[1], REQUEST_URL)
        self.assertEqual(mock_kwargs['data'], '[1, 2, 3]')
        self.assertEqual(mock_kwargs['headers']['X-Auth-Token'], 'token')
        self.assertEqual(mock_kwargs['cert'], ('cert.pem', 'key.pem'))
        self.assertEqual(mock_kwargs['verify'], 'ca.pem')
