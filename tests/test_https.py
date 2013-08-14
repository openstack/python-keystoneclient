import copy
import mock

import requests

from keystoneclient import httpclient
from tests import utils


FAKE_RESPONSE = utils.TestResponse({
    "status_code": 200,
    "text": '{"hi": "there"}',
})
MOCK_REQUEST = mock.Mock(return_value=(FAKE_RESPONSE))


def get_client():
    cl = httpclient.HTTPClient(username="username", password="password",
                               tenant_id="tenant", auth_url="auth_test",
                               cacert="ca.pem", key="key.pem", cert="cert.pem")
    return cl


def get_authed_client():
    cl = get_client()
    cl.management_url = "https://127.0.0.1:5000"
    cl.auth_token = "token"
    return cl


class ClientTest(utils.TestCase):

    def test_get(self):
        cl = get_authed_client()

        with mock.patch.object(requests, "request", MOCK_REQUEST):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp, body = cl.get("/hi")
                headers = {"X-Auth-Token": "token",
                           "User-Agent": httpclient.USER_AGENT}
                kwargs = copy.copy(self.TEST_REQUEST_BASE)
                kwargs['cert'] = ('cert.pem', 'key.pem')
                kwargs['verify'] = 'ca.pem'
                MOCK_REQUEST.assert_called_with(
                    "GET",
                    "https://127.0.0.1:5000/hi",
                    headers=headers,
                    **kwargs)
                # Automatic JSON parsing
                self.assertEqual(body, {"hi": "there"})

    def test_post(self):
        cl = get_authed_client()

        with mock.patch.object(requests, "request", MOCK_REQUEST):
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": httpclient.USER_AGENT
            }
            kwargs = copy.copy(self.TEST_REQUEST_BASE)
            kwargs['cert'] = ('cert.pem', 'key.pem')
            kwargs['verify'] = 'ca.pem'
            MOCK_REQUEST.assert_called_with(
                "POST",
                "https://127.0.0.1:5000/hi",
                headers=headers,
                data='[1, 2, 3]',
                **kwargs)

    def test_post_auth(self):
        with mock.patch.object(requests, "request", MOCK_REQUEST):
            cl = httpclient.HTTPClient(
                username="username", password="password", tenant_id="tenant",
                auth_url="auth_test", cacert="ca.pem", key="key.pem",
                cert="cert.pem")
            cl.management_url = "https://127.0.0.1:5000"
            cl.auth_token = "token"
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": httpclient.USER_AGENT
            }
            kwargs = copy.copy(self.TEST_REQUEST_BASE)
            kwargs['cert'] = ('cert.pem', 'key.pem')
            kwargs['verify'] = 'ca.pem'
            MOCK_REQUEST.assert_called_with(
                "POST",
                "https://127.0.0.1:5000/hi",
                headers=headers,
                data='[1, 2, 3]',
                **kwargs)
