import httplib2
import mock

from keystoneclient import client
from tests import utils


FAKE_RESPONSE = httplib2.Response({"status": 200})
FAKE_BODY = '{"hi": "there"}'
MOCK_REQUEST = mock.Mock(return_value=(FAKE_RESPONSE, FAKE_BODY))


def get_client():
    cl = client.HTTPClient(username="username", password="password",
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

        @mock.patch.object(httplib2.Http, "request", MOCK_REQUEST)
        @mock.patch('time.time', mock.Mock(return_value=1234))
        def test_get_call():
            resp, body = cl.get("/hi")
            headers = {"X-Auth-Token": "token",
                       "User-Agent": cl.USER_AGENT}
            MOCK_REQUEST.assert_called_with("https://127.0.0.1:5000/hi",
                                            "GET", headers=headers)
            # Automatic JSON parsing
            self.assertEqual(body, {"hi": "there"})

        test_get_call()

    def test_post(self):
        cl = get_authed_client()

        @mock.patch.object(httplib2.Http, "request", MOCK_REQUEST)
        def test_post_call():
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": cl.USER_AGENT
            }
            MOCK_REQUEST.assert_called_with("https://127.0.0.1:5000/hi",
                                            "POST", headers=headers,
                                            body='[1, 2, 3]')

        test_post_call()
