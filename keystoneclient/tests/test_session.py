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
import requests

from keystoneclient.auth import base
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


class RedirectTests(utils.TestCase):

    REDIRECT_CHAIN = ['http://myhost:3445/',
                      'http://anotherhost:6555/',
                      'http://thirdhost/',
                      'http://finaldestination:55/']

    DEFAULT_REDIRECT_BODY = 'Redirect'
    DEFAULT_RESP_BODY = 'Found'

    def setup_redirects(self, method=httpretty.GET, status=305,
                        redirect_kwargs={}, final_kwargs={}):
        redirect_kwargs.setdefault('body', self.DEFAULT_REDIRECT_BODY)

        for s, d in zip(self.REDIRECT_CHAIN, self.REDIRECT_CHAIN[1:]):
            httpretty.register_uri(method, s, status=status, location=d,
                                   **redirect_kwargs)

        final_kwargs.setdefault('status', 200)
        final_kwargs.setdefault('body', self.DEFAULT_RESP_BODY)
        httpretty.register_uri(method, self.REDIRECT_CHAIN[-1], **final_kwargs)

    def assertResponse(self, resp):
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, self.DEFAULT_RESP_BODY)

    @httpretty.activate
    def test_basic_get(self):
        session = client_session.Session()
        self.setup_redirects()
        resp = session.get(self.REDIRECT_CHAIN[-2])
        self.assertResponse(resp)

    @httpretty.activate
    def test_basic_post_keeps_correct_method(self):
        session = client_session.Session()
        self.setup_redirects(method=httpretty.POST, status=301)
        resp = session.post(self.REDIRECT_CHAIN[-2])
        self.assertResponse(resp)

    @httpretty.activate
    def test_redirect_forever(self):
        session = client_session.Session(redirect=True)
        self.setup_redirects()
        resp = session.get(self.REDIRECT_CHAIN[0])
        self.assertResponse(resp)
        self.assertTrue(len(resp.history), len(self.REDIRECT_CHAIN))

    @httpretty.activate
    def test_no_redirect(self):
        session = client_session.Session(redirect=False)
        self.setup_redirects()
        resp = session.get(self.REDIRECT_CHAIN[0])
        self.assertEqual(resp.status_code, 305)
        self.assertEqual(resp.url, self.REDIRECT_CHAIN[0])

    @httpretty.activate
    def test_redirect_limit(self):
        self.setup_redirects()
        for i in (1, 2):
            session = client_session.Session(redirect=i)
            resp = session.get(self.REDIRECT_CHAIN[0])
            self.assertEqual(resp.status_code, 305)
            self.assertEqual(resp.url, self.REDIRECT_CHAIN[i])
            self.assertEqual(resp.text, self.DEFAULT_REDIRECT_BODY)

    @httpretty.activate
    def test_history_matches_requests(self):
        self.setup_redirects(status=301)
        session = client_session.Session(redirect=True)
        req_resp = requests.get(self.REDIRECT_CHAIN[0],
                                allow_redirects=True)

        ses_resp = session.get(self.REDIRECT_CHAIN[0])

        self.assertEqual(type(req_resp.history), type(ses_resp.history))
        self.assertEqual(len(req_resp.history), len(ses_resp.history))

        for r, s in zip(req_resp.history, ses_resp.history):
            self.assertEqual(r.url, s.url)
            self.assertEqual(r.status_code, s.status_code)


class ConstructSessionFromArgsTests(utils.TestCase):

    KEY = 'keyfile'
    CERT = 'certfile'
    CACERT = 'cacert-path'

    def _s(self, k=None, **kwargs):
        k = k or kwargs
        return client_session.Session.construct(k)

    def test_verify(self):
        self.assertFalse(self._s(insecure=True).verify)
        self.assertTrue(self._s(verify=True, insecure=True).verify)
        self.assertFalse(self._s(verify=False, insecure=True).verify)
        self.assertEqual(self._s(cacert=self.CACERT).verify, self.CACERT)

    def test_cert(self):
        tup = (self.CERT, self.KEY)
        self.assertEqual(self._s(cert=tup).cert, tup)
        self.assertEqual(self._s(cert=self.CERT, key=self.KEY).cert, tup)
        self.assertIsNone(self._s(key=self.KEY).cert)

    def test_pass_through(self):
        value = 42  # only a number because timeout needs to be
        for key in ['timeout', 'session', 'original_ip', 'user_agent']:
            args = {key: value}
            self.assertEqual(getattr(self._s(args), key), value)
            self.assertNotIn(key, args)


class AuthPlugin(base.BaseAuthPlugin):
    """Very simple debug authentication plugin.

    Takes Parameters such that it can throw exceptions at the right times.
    """

    TEST_TOKEN = 'aToken'

    def __init__(self, token=TEST_TOKEN):
        self.token = token

    def get_token(self, session):
        return self.token


class SessionAuthTests(utils.TestCase):

    TEST_URL = 'http://127.0.0.1:5000/'
    TEST_JSON = {'hello': 'world'}

    @httpretty.activate
    def test_auth_plugin_default_with_plugin(self):
        self.stub_url('GET', base_url=self.TEST_URL, json=self.TEST_JSON)

        # if there is an auth_plugin then it should default to authenticated
        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)
        resp = sess.get(self.TEST_URL)
        self.assertDictEqual(resp.json(), self.TEST_JSON)

        self.assertRequestHeaderEqual('X-Auth-Token', AuthPlugin.TEST_TOKEN)

    @httpretty.activate
    def test_auth_plugin_disable(self):
        self.stub_url('GET', base_url=self.TEST_URL, json=self.TEST_JSON)

        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)
        resp = sess.get(self.TEST_URL, authenticated=False)
        self.assertDictEqual(resp.json(), self.TEST_JSON)

        self.assertRequestHeaderEqual('X-Auth-Token', None)
