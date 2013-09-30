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
import mock

from keystoneclient import exceptions
from keystoneclient import session as client_session
from keystoneclient.tests import utils


class SessionTests(utils.TestCase):

    TEST_URL = 'http://127.0.0.1:5000/'

    @httpretty.activate
    def test_get(self):
        session = client_session.Session()
        self.stub_url(httpretty.GET, body='response')
        resp = session.get(self.TEST_URL)

        self.assertEqual(httpretty.GET, httpretty.last_request().method)
        self.assertEqual(resp.text, 'response')
        self.assertTrue(resp.ok)

    @httpretty.activate
    def test_post(self):
        session = client_session.Session()
        self.stub_url(httpretty.POST, body='response')
        resp = session.post(self.TEST_URL, json={'hello': 'world'})

        self.assertEqual(httpretty.POST, httpretty.last_request().method)
        self.assertEqual(resp.text, 'response')
        self.assertTrue(resp.ok)
        self.assertRequestBodyIs(json={'hello': 'world'})

    @httpretty.activate
    def test_head(self):
        session = client_session.Session()
        self.stub_url(httpretty.HEAD)
        resp = session.head(self.TEST_URL)

        self.assertEqual(httpretty.HEAD, httpretty.last_request().method)
        self.assertTrue(resp.ok)
        self.assertRequestBodyIs('')

    @httpretty.activate
    def test_put(self):
        session = client_session.Session()
        self.stub_url(httpretty.PUT, body='response')
        resp = session.put(self.TEST_URL, json={'hello': 'world'})

        self.assertEqual(httpretty.PUT, httpretty.last_request().method)
        self.assertEqual(resp.text, 'response')
        self.assertTrue(resp.ok)
        self.assertRequestBodyIs(json={'hello': 'world'})

    @httpretty.activate
    def test_delete(self):
        session = client_session.Session()
        self.stub_url(httpretty.DELETE, body='response')
        resp = session.delete(self.TEST_URL)

        self.assertEqual(httpretty.DELETE, httpretty.last_request().method)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.text, 'response')

    @httpretty.activate
    def test_patch(self):
        session = client_session.Session()
        self.stub_url(httpretty.PATCH, body='response')
        resp = session.patch(self.TEST_URL, json={'hello': 'world'})

        self.assertEqual(httpretty.PATCH, httpretty.last_request().method)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.text, 'response')
        self.assertRequestBodyIs(json={'hello': 'world'})

    @httpretty.activate
    def test_user_agent(self):
        session = client_session.Session(user_agent='test-agent')
        self.stub_url(httpretty.GET, body='response')
        resp = session.get(self.TEST_URL)

        self.assertTrue(resp.ok)
        self.assertRequestHeaderEqual('User-Agent', 'test-agent')

        resp = session.get(self.TEST_URL, headers={'User-Agent': 'new-agent'})
        self.assertTrue(resp.ok)
        self.assertRequestHeaderEqual('User-Agent', 'new-agent')

        resp = session.get(self.TEST_URL, headers={'User-Agent': 'new-agent'},
                           user_agent='overrides-agent')
        self.assertTrue(resp.ok)
        self.assertRequestHeaderEqual('User-Agent', 'overrides-agent')

    @httpretty.activate
    def test_http_session_opts(self):
        session = client_session.Session(cert='cert.pem', timeout=5,
                                         verify='certs')

        FAKE_RESP = utils.TestResponse({'status_code': 200, 'text': 'resp'})
        RESP = mock.Mock(return_value=FAKE_RESP)

        with mock.patch.object(session.session, 'request', RESP) as mocked:
            session.post(self.TEST_URL, data='value')

            mock_args, mock_kwargs = mocked.call_args

            self.assertEqual(mock_args[0], 'POST')
            self.assertEqual(mock_args[1], self.TEST_URL)
            self.assertEqual(mock_kwargs['data'], 'value')
            self.assertEqual(mock_kwargs['cert'], 'cert.pem')
            self.assertEqual(mock_kwargs['verify'], 'certs')
            self.assertEqual(mock_kwargs['timeout'], 5)

    @httpretty.activate
    def test_not_found(self):
        session = client_session.Session()
        self.stub_url(httpretty.GET, status=404)
        self.assertRaises(exceptions.NotFound, session.get, self.TEST_URL)

    @httpretty.activate
    def test_server_error(self):
        session = client_session.Session()
        self.stub_url(httpretty.GET, status=500)
        self.assertRaises(exceptions.InternalServerError,
                          session.get, self.TEST_URL)
