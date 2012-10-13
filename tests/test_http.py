import httplib2
import mock

from keystoneclient import client
from keystoneclient import exceptions
from tests import utils


fake_response = httplib2.Response({"status": 200})
fake_body = '{"hi": "there"}'
mock_request = mock.Mock(return_value=(fake_response, fake_body))


def get_client():
    cl = client.HTTPClient(username="username", password="password",
                           tenant_id="tenant", auth_url="auth_test")
    return cl


def get_authed_client():
    cl = get_client()
    cl.management_url = "http://127.0.0.1:5000"
    cl.auth_token = "token"
    return cl


class ClientTest(utils.TestCase):

    def test_unauthorized_client_requests(self):
        cl = get_client()
        self.assertRaises(exceptions.AuthorizationFailure, cl.get, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.post, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.put, '/hi')
        self.assertRaises(exceptions.AuthorizationFailure, cl.delete, '/hi')

    def test_get(self):
        cl = get_authed_client()

        with mock.patch.object(httplib2.Http, "request", mock_request):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp, body = cl.get("/hi")
                headers = {"X-Auth-Token": "token",
                           "User-Agent": cl.USER_AGENT}
                mock_request.assert_called_with("http://127.0.0.1:5000/hi",
                                                "GET", headers=headers)
                # Automatic JSON parsing
                self.assertEqual(body, {"hi": "there"})

    def test_get_error(self):
        cl = get_authed_client()

        fake_err_response = httplib2.Response({"status": 400})
        fake_err_body = 'Some evil plaintext string'
        err_mock_request = mock.Mock(return_value=(fake_err_response,
                                                   fake_err_body))

        with mock.patch.object(httplib2.Http, "request", err_mock_request):
            self.assertRaises(exceptions.BadRequest, cl.get, '/hi')

    def test_post(self):
        cl = get_authed_client()

        with mock.patch.object(httplib2.Http, "request", mock_request):
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": cl.USER_AGENT
            }
            mock_request.assert_called_with("http://127.0.0.1:5000/hi", "POST",
                                            headers=headers, body='[1, 2, 3]')

    def test_forwarded_for(self):
        ORIGINAL_IP = "10.100.100.1"
        cl = client.HTTPClient(username="username", password="password",
                               tenant_id="tenant", auth_url="auth_test",
                               original_ip=ORIGINAL_IP)

        with mock.patch.object(httplib2.Http, "request", mock_request):
            res = cl.request('/', 'GET')

            args, kwargs = mock_request.call_args
            self.assertIn(
                ('Forwarded', "for=%s;by=%s" % (ORIGINAL_IP, cl.USER_AGENT)),
                kwargs['headers'].items())
