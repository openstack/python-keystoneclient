# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack LLC
#
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

import json
import mock

import httpretty
import requests
import testtools
from testtools import matchers

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


class FakeLog(object):
    def __init__(self):
        self.warn_log = str()
        self.debug_log = str()

    def warn(self, msg=None, *args, **kwargs):
        self.warn_log = "%s\n%s" % (self.warn_log, (msg % args))

    def debug(self, msg=None, *args, **kwargs):
        self.debug_log = "%s\n%s" % (self.debug_log, (msg % args))


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
                           "User-Agent": httpclient.USER_AGENT}
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
            "text": json.dumps(err_response),
            "headers": {"Content-Type": "application/json"},
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
                "User-Agent": httpclient.USER_AGENT
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
            cl.request('/', 'GET')

            args, kwargs = MOCK_REQUEST.call_args
            self.assertIn(
                ('Forwarded', "for=%s;by=%s" % (ORIGINAL_IP,
                                                httpclient.USER_AGENT)),
                kwargs['headers'].items())

    def test_client_deprecated(self):
        # Can resolve symbols from the keystoneclient.client module.
        # keystoneclient.client was deprecated and renamed to
        # keystoneclient.httpclient. This tests that keystoneclient.client
        # can still be used.

        from keystoneclient import client

        # These statements will raise an AttributeError if the symbol isn't
        # defined in the module.

        client.HTTPClient


class BasicRequestTests(testtools.TestCase):

    url = 'http://keystone.test.com/'

    def setUp(self):
        super(BasicRequestTests, self).setUp()
        self.logger = FakeLog()
        httpretty.enable()

    def tearDown(self):
        httpretty.disable()
        super(BasicRequestTests, self).tearDown()

    def request(self, method='GET', response='Test Response', status=200,
                url=None, **kwargs):
        if not url:
            url = self.url

        httpretty.register_uri(method, url, body=response, status=status)

        return httpclient.request(url, method, debug=True,
                                  logger=self.logger, **kwargs)

    @property
    def last_request(self):
        return httpretty.httpretty.last_request

    def test_basic_params(self):
        method = 'GET'
        response = 'Test Response'
        status = 200

        self.request(method=method, status=status, response=response)

        self.assertEqual(self.last_request.method, method)

        self.assertThat(self.logger.debug_log, matchers.Contains('curl'))
        self.assertThat(self.logger.debug_log, matchers.Contains('-X %s' %
                                                                 method))
        self.assertThat(self.logger.debug_log, matchers.Contains(self.url))

        self.assertThat(self.logger.debug_log, matchers.Contains(str(status)))
        self.assertThat(self.logger.debug_log, matchers.Contains(response))

    def test_headers(self):
        headers = {'key': 'val', 'test': 'other'}

        self.request(headers=headers)

        for k, v in headers.iteritems():
            self.assertEqual(self.last_request.headers[k], v)

        for header in headers.iteritems():
            self.assertThat(self.logger.debug_log,
                            matchers.Contains('-H "%s: %s"' % header))

    def test_body(self):
        data = "BODY DATA"
        self.request(response=data)
        self.assertThat(self.logger.debug_log, matchers.Contains('BODY:'))
        self.assertThat(self.logger.debug_log, matchers.Contains(data))
