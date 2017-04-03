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

import logging
import sys
import uuid

import fixtures
from oslo_serialization import jsonutils
import requests
import requests_mock
from requests_mock.contrib import fixture
from six.moves.urllib import parse as urlparse
import testscenarios
import testtools

from keystoneclient.tests.unit import client_fixtures


class TestCase(testtools.TestCase):

    TEST_DOMAIN_ID = uuid.uuid4().hex
    TEST_DOMAIN_NAME = uuid.uuid4().hex
    TEST_GROUP_ID = uuid.uuid4().hex
    TEST_ROLE_ID = uuid.uuid4().hex
    TEST_TENANT_ID = uuid.uuid4().hex
    TEST_TENANT_NAME = uuid.uuid4().hex
    TEST_TOKEN = uuid.uuid4().hex
    TEST_TRUST_ID = uuid.uuid4().hex
    TEST_USER = uuid.uuid4().hex
    TEST_USER_ID = uuid.uuid4().hex

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'

    def setUp(self):
        super(TestCase, self).setUp()
        self.deprecations = self.useFixture(client_fixtures.Deprecations())

        self.logger = self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        self.requests_mock = self.useFixture(fixture.Fixture())

    def stub_url(self, method, parts=None, base_url=None, json=None, **kwargs):
        if not base_url:
            base_url = self.TEST_URL

        if json:
            kwargs['text'] = jsonutils.dumps(json)
            headers = kwargs.setdefault('headers', {})
            headers['Content-Type'] = 'application/json'

        if parts:
            url = '/'.join([p.strip('/') for p in [base_url] + parts])
        else:
            url = base_url

        url = url.replace("/?", "?")
        self.requests_mock.register_uri(method, url, **kwargs)

    def assertRequestBodyIs(self, body=None, json=None):
        last_request_body = self.requests_mock.last_request.body
        if json:
            val = jsonutils.loads(last_request_body)
            self.assertEqual(json, val)
        elif body:
            self.assertEqual(body, last_request_body)

    def assertQueryStringIs(self, qs=''):
        r"""Verify the QueryString matches what is expected.

        The qs parameter should be of the format \'foo=bar&abc=xyz\'
        """
        expected = urlparse.parse_qs(qs, keep_blank_values=True)
        parts = urlparse.urlparse(self.requests_mock.last_request.url)
        querystring = urlparse.parse_qs(parts.query, keep_blank_values=True)
        self.assertEqual(expected, querystring)

    def assertQueryStringContains(self, **kwargs):
        """Verify the query string contains the expected parameters.

        This method is used to verify that the query string for the most recent
        request made contains all the parameters provided as ``kwargs``, and
        that the value of each parameter contains the value for the kwarg. If
        the value for the kwarg is an empty string (''), then all that's
        verified is that the parameter is present.

        """
        parts = urlparse.urlparse(self.requests_mock.last_request.url)
        qs = urlparse.parse_qs(parts.query, keep_blank_values=True)

        for k, v in kwargs.items():
            self.assertIn(k, qs)
            self.assertIn(v, qs[k])

    def assertRequestHeaderEqual(self, name, val):
        """Verify that the last request made contains a header and its value.

        The request must have already been made.
        """
        headers = self.requests_mock.last_request.headers
        self.assertEqual(headers.get(name), val)


def test_response(**kwargs):
    r = requests.Request(method='GET', url='http://localhost:5000').prepare()
    return requests_mock.create_response(r, **kwargs)


class DisableModuleFixture(fixtures.Fixture):
    """A fixture to provide support for unloading/disabling modules."""

    def __init__(self, module, *args, **kw):
        super(DisableModuleFixture, self).__init__(*args, **kw)
        self.module = module
        self._finders = []
        self._cleared_modules = {}

    def tearDown(self):
        super(DisableModuleFixture, self).tearDown()
        for finder in self._finders:
            sys.meta_path.remove(finder)
        sys.modules.update(self._cleared_modules)

    def clear_module(self):
        cleared_modules = {}
        for fullname in list(sys.modules):
            if (fullname == self.module or
                    fullname.startswith(self.module + '.')):
                cleared_modules[fullname] = sys.modules.pop(fullname)
        return cleared_modules

    def setUp(self):
        """Ensure ImportError for the specified module."""
        super(DisableModuleFixture, self).setUp()

        # Clear 'module' references in sys.modules
        self._cleared_modules.update(self.clear_module())

        finder = NoModuleFinder(self.module)
        self._finders.append(finder)
        sys.meta_path.insert(0, finder)


class ClientTestCaseMixin(testscenarios.WithScenarios):

    client_fixture_class = None
    data_fixture_class = None

    def setUp(self):
        super(ClientTestCaseMixin, self).setUp()

        self.data_fixture = None
        self.client_fixture = None
        self.client = None

        if self.client_fixture_class:
            fix = self.client_fixture_class(self.requests_mock,
                                            self.deprecations)
            self.client_fixture = self.useFixture(fix)
            self.client = self.client_fixture.client
            self.TEST_USER_ID = self.client_fixture.user_id

        if self.data_fixture_class:
            fix = self.data_fixture_class(self.requests_mock)
            self.data_fixture = self.useFixture(fix)


class NoModuleFinder(object):
    """Disallow further imports of 'module'."""

    def __init__(self, module):
        self.module = module

    def find_module(self, fullname, path):
        if fullname == self.module or fullname.startswith(self.module + '.'):
            raise ImportError
