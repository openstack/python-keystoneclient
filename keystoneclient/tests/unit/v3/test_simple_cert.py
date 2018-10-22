# Copyright 2014 IBM Corp.
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import fixtures
import testresources

from keystoneclient.tests.unit import client_fixtures
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3.contrib import simple_cert


class SimpleCertTests(utils.ClientTestCase, testresources.ResourcedTestCase):

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def test_get_ca_certificate(self):
        self.stub_url('GET', ['OS-SIMPLE-CERT', 'ca'],
                      headers={'Content-Type': 'application/x-pem-file'},
                      text=self.examples.SIGNING_CA)
        res = self.client.simple_cert.get_ca_certificates()
        self.assertEqual(self.examples.SIGNING_CA, res)

    def test_get_certificates(self):
        self.stub_url('GET', ['OS-SIMPLE-CERT', 'certificates'],
                      headers={'Content-Type': 'application/x-pem-file'},
                      text=self.examples.SIGNING_CERT)
        res = self.client.simple_cert.get_certificates()
        self.assertEqual(self.examples.SIGNING_CERT, res)


class SimpleCertRequestIdTests(utils.TestRequestId):

    def setUp(self):
        super(SimpleCertRequestIdTests, self).setUp()
        self.mgr = simple_cert.SimpleCertManager(self.client)

    def _mock_request_method(self, method=None, body=None):
        return self.useFixture(fixtures.MockPatchObject(
            self.client, method, autospec=True,
            return_value=(self.resp, body))
        ).mock

    def test_list_ca_certificates(self):
        body = {"certificates": [{"name": "admin"}, {"name": "admin2"}]}
        get_mock = self._mock_request_method(method='get', body=body)

        response = self.mgr.get_ca_certificates()
        self.assertEqual(response.request_ids[0], self.TEST_REQUEST_ID)
        get_mock.assert_called_once_with(
            '/OS-SIMPLE-CERT/ca', authenticated=False)

    def test_list_certificates(self):
        body = {"certificates": [{"name": "admin"}, {"name": "admin2"}]}
        get_mock = self._mock_request_method(method='get', body=body)

        response = self.mgr.get_certificates()
        self.assertEqual(response.request_ids[0], self.TEST_REQUEST_ID)
        get_mock.assert_called_once_with(
            '/OS-SIMPLE-CERT/certificates', authenticated=False)


def load_tests(loader, tests, pattern):
    return testresources.OptimisingTestSuite(tests)
