# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import sys
import time

import httpretty
import mock
from mox3 import mox
import requests
import testtools

from keystoneclient.openstack.common import jsonutils


class TestCase(testtools.TestCase):
    TEST_DOMAIN_ID = '1'
    TEST_DOMAIN_NAME = 'aDomain'
    TEST_TENANT_ID = '1'
    TEST_TENANT_NAME = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'

    def setUp(self):
        super(TestCase, self).setUp()
        self.mox = mox.Mox()
        self.time_patcher = mock.patch.object(time, 'time', lambda: 1234)
        self.time_patcher.start()

    def tearDown(self):
        self.time_patcher.stop()
        self.mox.UnsetStubs()
        self.mox.VerifyAll()
        super(TestCase, self).tearDown()

    def stub_url(self, method, parts=None, base_url=None, json=None, **kwargs):
        if not base_url:
            base_url = self.TEST_URL

        if json:
            kwargs['body'] = jsonutils.dumps(json)
            kwargs['content_type'] = 'application/json'

        if parts:
            url = '/'.join([p.strip('/') for p in [base_url] + parts])
        else:
            url = base_url

        httpretty.register_uri(method, url, **kwargs)

    def assertRequestBodyIs(self, body=None, json=None):
        if json:
            val = jsonutils.loads(httpretty.last_request().body)
            self.assertEqual(json, val)
        elif body:
            self.assertEqual(body, httpretty.last_request().body)

    def assertQueryStringIs(self, val):
        self.assertEqual(httpretty.last_request().querystring, val)


if tuple(sys.version_info)[0:2] < (2, 7):

    def assertDictEqual(self, d1, d2, msg=None):
        # Simple version taken from 2.7
        self.assertIsInstance(d1, dict,
                              'First argument is not a dictionary')
        self.assertIsInstance(d2, dict,
                              'Second argument is not a dictionary')
        if d1 != d2:
            if msg:
                self.fail(msg)
            else:
                standardMsg = '%r != %r' % (d1, d2)
                self.fail(standardMsg)

    TestCase.assertDictEqual = assertDictEqual


class TestResponse(requests.Response):
    """Class used to wrap requests.Response and provide some
       convenience to initialize with a dict.
    """

    def __init__(self, data):
        self._text = None
        super(TestResponse, self).__init__()
        if isinstance(data, dict):
            self.status_code = data.get('status_code', None)
            headers = data.get('headers')
            if headers:
                self.headers.update(headers)
            # Fake the text attribute to streamline Response creation
            # _content is defined by requests.Response
            self._content = data.get('text', None)
        else:
            self.status_code = data

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def text(self):
        return self.content
