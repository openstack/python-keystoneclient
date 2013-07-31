import json
import mock

import requests

from keystoneclient import exceptions
from keystoneclient import httpclient
from tests import utils


FAKE_RESPONSE = utils.TestResponse({
    "status_code": 200,
    "text": '{"hi": "there"}',
})
MOCK_REQUEST = mock.Mock(return_value=(FAKE_RESPONSE))


def get_client():
    cl = httpclient.HTTPClient(username="username", password="password",
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

        with mock.patch.object(requests, "request", MOCK_REQUEST):
            with mock.patch('time.time', mock.Mock(return_value=1234)):
                resp, body = cl.get("/hi")
                headers = {"X-Auth-Token": "token",
                           "User-Agent": cl.USER_AGENT}
                MOCK_REQUEST.assert_called_with(
                    "GET",
                    "http://127.0.0.1:5000/hi",
                    headers=headers,
                    **self.TEST_REQUEST_BASE)
                # Automatic JSON parsing
                self.assertEqual(body, {"hi": "there"})

    def test_get_error_with_plaintext_resp(self):
        cl = get_authed_client()

        fake_err_response = utils.TestResponse({
            "status_code": 400,
            "text": 'Some evil plaintext string',
        })
        err_MOCK_REQUEST = mock.Mock(return_value=(fake_err_response))

        with mock.patch.object(requests, "request", err_MOCK_REQUEST):
            self.assertRaises(exceptions.BadRequest, cl.get, '/hi')

    def test_get_error_with_json_resp(self):
        cl = get_authed_client()
        err_response = {
            "error": {
                "code": 400,
                "title": "Error title",
                "message": "Error message string"
            }
        }
        fake_err_response = utils.TestResponse({
            "status_code": 400,
            "text": json.dumps(err_response)
        })
        err_MOCK_REQUEST = mock.Mock(return_value=(fake_err_response))

        with mock.patch.object(requests, "request", err_MOCK_REQUEST):
            exc_raised = False
            try:
                cl.get('/hi')
            except exceptions.BadRequest as exc:
                exc_raised = True
                self.assertEqual(exc.message, "Error message string")
            self.assertTrue(exc_raised, 'Exception not raised.')

    def test_post(self):
        cl = get_authed_client()

        with mock.patch.object(requests, "request", MOCK_REQUEST):
            cl.post("/hi", body=[1, 2, 3])
            headers = {
                "X-Auth-Token": "token",
                "Content-Type": "application/json",
                "User-Agent": cl.USER_AGENT
            }
            MOCK_REQUEST.assert_called_with(
                "POST",
                "http://127.0.0.1:5000/hi",
                headers=headers,
                data='[1, 2, 3]',
                **self.TEST_REQUEST_BASE)

    def test_forwarded_for(self):
        ORIGINAL_IP = "10.100.100.1"
        cl = httpclient.HTTPClient(username="username", password="password",
                                   tenant_id="tenant", auth_url="auth_test",
                                   original_ip=ORIGINAL_IP)

        with mock.patch.object(requests, "request", MOCK_REQUEST):
            res = cl.request('/', 'GET')

            args, kwargs = MOCK_REQUEST.call_args
            self.assertIn(
                ('Forwarded', "for=%s;by=%s" % (ORIGINAL_IP, cl.USER_AGENT)),
                kwargs['headers'].items())
