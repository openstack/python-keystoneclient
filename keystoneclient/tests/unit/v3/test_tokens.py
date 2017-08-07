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

import uuid

from keystoneauth1 import exceptions
import testresources

from keystoneclient import access
from keystoneclient.tests.unit import client_fixtures
from keystoneclient.tests.unit.v3 import utils


class TokenTests(utils.ClientTestCase, testresources.ResourcedTestCase):

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def test_revoke_token_with_token_id(self):
        token_id = uuid.uuid4().hex
        self.stub_url('DELETE', ['/auth/tokens'], status_code=204)
        self.client.tokens.revoke_token(token_id)
        self.assertRequestHeaderEqual('X-Subject-Token', token_id)

    def test_revoke_token_with_access_info_instance(self):
        token_id = uuid.uuid4().hex
        token_ref = self.examples.TOKEN_RESPONSES[
            self.examples.v3_UUID_TOKEN_DEFAULT]
        token = access.AccessInfoV3(token_id, token_ref['token'])
        self.stub_url('DELETE', ['/auth/tokens'], status_code=204)
        self.client.tokens.revoke_token(token)
        self.assertRequestHeaderEqual('X-Subject-Token', token_id)

    def test_get_revoked(self):
        sample_revoked_response = {'signed': '-----BEGIN CMS-----\nMIIB...'}
        self.stub_url('GET', ['auth', 'tokens', 'OS-PKI', 'revoked'],
                      json=sample_revoked_response)
        resp = self.client.tokens.get_revoked()
        self.assertQueryStringIs()
        self.assertEqual(sample_revoked_response, resp)

    def test_get_revoked_audit_id_only(self):
        # When get_revoked(audit_id_only=True) then ?audit_id_only is set on
        # the request.
        sample_revoked_response = {
            'revoked': [
                {
                    'audit_id': uuid.uuid4().hex,
                    'expires': '2016-01-21T15:53:52Z',
                },
            ],
        }
        self.stub_url('GET', ['auth', 'tokens', 'OS-PKI', 'revoked'],
                      json=sample_revoked_response)
        resp = self.client.tokens.get_revoked(audit_id_only=True)
        self.assertQueryStringIs('audit_id_only')
        self.assertEqual(sample_revoked_response, resp)

    def test_validate_token_with_token_id(self):
        # Can validate a token passing a string token ID.
        token_id = uuid.uuid4().hex
        token_ref = self.examples.TOKEN_RESPONSES[
            self.examples.v3_UUID_TOKEN_DEFAULT]
        self.stub_url('GET', ['auth', 'tokens'],
                      headers={'X-Subject-Token': token_id, }, json=token_ref)

        token_data = self.client.tokens.get_token_data(token_id)
        self.assertEqual(token_data, token_ref)

        access_info = self.client.tokens.validate(token_id)

        self.assertRequestHeaderEqual('X-Subject-Token', token_id)
        self.assertIsInstance(access_info, access.AccessInfoV3)
        self.assertEqual(token_id, access_info.auth_token)

    def test_validate_token_with_access_info(self):
        # Can validate a token passing an access info.
        token_id = uuid.uuid4().hex
        token_ref = self.examples.TOKEN_RESPONSES[
            self.examples.v3_UUID_TOKEN_DEFAULT]
        token = access.AccessInfoV3(token_id, token_ref['token'])
        self.stub_url('GET', ['auth', 'tokens'],
                      headers={'X-Subject-Token': token_id, }, json=token_ref)
        access_info = self.client.tokens.validate(token)

        self.assertRequestHeaderEqual('X-Subject-Token', token_id)
        self.assertIsInstance(access_info, access.AccessInfoV3)
        self.assertEqual(token_id, access_info.auth_token)

    def test_validate_token_invalid(self):
        # When the token is invalid the server typically returns a 404.
        token_id = uuid.uuid4().hex
        self.stub_url('GET', ['auth', 'tokens'], status_code=404)

        self.assertRaises(exceptions.NotFound,
                          self.client.tokens.get_token_data, token_id)
        self.assertRaises(exceptions.NotFound,
                          self.client.tokens.validate, token_id)

    def test_validate_token_catalog(self):
        # Can validate a token and a catalog is requested by default.
        token_id = uuid.uuid4().hex
        token_ref = self.examples.TOKEN_RESPONSES[
            self.examples.v3_UUID_TOKEN_DEFAULT]
        self.stub_url('GET', ['auth', 'tokens'],
                      headers={'X-Subject-Token': token_id, }, json=token_ref)

        token_data = self.client.tokens.get_token_data(token_id)
        self.assertQueryStringIs()
        self.assertIn('catalog', token_data['token'])

        access_info = self.client.tokens.validate(token_id)

        self.assertQueryStringIs()
        self.assertTrue(access_info.has_service_catalog())

    def test_validate_token_nocatalog(self):
        # Can validate a token and request no catalog.
        token_id = uuid.uuid4().hex
        token_ref = self.examples.TOKEN_RESPONSES[
            self.examples.v3_UUID_TOKEN_UNSCOPED]
        self.stub_url('GET', ['auth', 'tokens'],
                      headers={'X-Subject-Token': token_id, }, json=token_ref)

        token_data = self.client.tokens.get_token_data(token_id)
        self.assertQueryStringIs()
        self.assertNotIn('catalog', token_data['token'])

        access_info = self.client.tokens.validate(token_id,
                                                  include_catalog=False)

        self.assertQueryStringIs('nocatalog')
        self.assertFalse(access_info.has_service_catalog())

    def test_validate_token_allow_expired(self):
        token_id = uuid.uuid4().hex
        token_ref = self.examples.TOKEN_RESPONSES[
            self.examples.v3_UUID_TOKEN_UNSCOPED]
        self.stub_url('GET', ['auth', 'tokens'],
                      headers={'X-Subject-Token': token_id, }, json=token_ref)

        self.client.tokens.validate(token_id)
        self.assertQueryStringIs()

        self.client.tokens.validate(token_id, allow_expired=True)
        self.assertQueryStringIs('allow_expired=1')


def load_tests(loader, tests, pattern):
    return testresources.OptimisingTestSuite(tests)
