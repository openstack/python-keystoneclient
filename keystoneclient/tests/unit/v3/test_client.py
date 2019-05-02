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

import copy
import uuid

from oslo_serialization import jsonutils

from keystoneauth1 import session as auth_session
from keystoneclient.auth import token_endpoint
from keystoneclient import exceptions
from keystoneclient import session
from keystoneclient.tests.unit.v3 import client_fixtures
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import client


class KeystoneClientTest(utils.TestCase):

    def test_unscoped_init(self):
        token = client_fixtures.unscoped_token()
        self.stub_auth(json=token)

        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            c = client.Client(user_domain_name=token.user_domain_name,
                              username=token.user_name,
                              password='password',
                              auth_url=self.TEST_URL)
        self.assertIsNotNone(c.auth_ref)
        self.assertFalse(c.auth_ref.domain_scoped)
        self.assertFalse(c.auth_ref.project_scoped)
        self.assertEqual(token.user_id, c.auth_user_id)
        self.assertFalse(c.has_service_catalog())

        self.assertEqual(token.user_id, c.get_user_id(session=None))
        self.assertIsNone(c.get_project_id(session=None))

    def test_domain_scoped_init(self):
        token = client_fixtures.domain_scoped_token()
        self.stub_auth(json=token)

        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            c = client.Client(user_id=token.user_id,
                              password='password',
                              domain_name=token.domain_name,
                              auth_url=self.TEST_URL)
        self.assertIsNotNone(c.auth_ref)
        self.assertTrue(c.auth_ref.domain_scoped)
        self.assertFalse(c.auth_ref.project_scoped)
        self.assertEqual(token.user_id, c.auth_user_id)
        self.assertEqual(token.domain_id, c.auth_domain_id)

    def test_project_scoped_init(self):
        token = client_fixtures.project_scoped_token()
        self.stub_auth(json=token),

        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            c = client.Client(user_id=token.user_id,
                              password='password',
                              user_domain_name=token.user_domain_name,
                              project_name=token.project_name,
                              auth_url=self.TEST_URL)
        self.assertIsNotNone(c.auth_ref)
        self.assertFalse(c.auth_ref.domain_scoped)
        self.assertTrue(c.auth_ref.project_scoped)
        self.assertEqual(token.user_id, c.auth_user_id)
        self.assertEqual(token.project_id, c.auth_tenant_id)
        self.assertEqual(token.user_id, c.get_user_id(session=None))
        self.assertEqual(token.project_id, c.get_project_id(session=None))

    def test_auth_ref_load(self):
        token = client_fixtures.project_scoped_token()
        self.stub_auth(json=token)

        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            c = client.Client(user_id=token.user_id,
                              password='password',
                              project_id=token.project_id,
                              auth_url=self.TEST_URL)
        cache = jsonutils.dumps(c.auth_ref)
        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            new_client = client.Client(auth_ref=jsonutils.loads(cache))
        self.assertIsNotNone(new_client.auth_ref)
        self.assertFalse(new_client.auth_ref.domain_scoped)
        self.assertTrue(new_client.auth_ref.project_scoped)
        self.assertEqual(token.user_name, new_client.username)
        self.assertIsNone(new_client.password)
        self.assertEqual(new_client.management_url,
                         'http://admin:35357/v3')

    def test_auth_ref_load_with_overridden_arguments(self):
        new_auth_url = 'https://newkeystone.com/v3'

        user_id = uuid.uuid4().hex
        user_name = uuid.uuid4().hex
        project_id = uuid.uuid4().hex

        first = client_fixtures.project_scoped_token(user_id=user_id,
                                                     user_name=user_name,
                                                     project_id=project_id)
        second = client_fixtures.project_scoped_token(user_id=user_id,
                                                      user_name=user_name,
                                                      project_id=project_id)
        self.stub_auth(json=first)
        self.stub_auth(json=second, base_url=new_auth_url)

        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            c = client.Client(user_id=user_id,
                              password='password',
                              project_id=project_id,
                              auth_url=self.TEST_URL)
        cache = jsonutils.dumps(c.auth_ref)
        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            new_client = client.Client(auth_ref=jsonutils.loads(cache),
                                       auth_url=new_auth_url)
        self.assertIsNotNone(new_client.auth_ref)
        self.assertFalse(new_client.auth_ref.domain_scoped)
        self.assertTrue(new_client.auth_ref.project_scoped)
        self.assertEqual(new_auth_url, new_client.auth_url)
        self.assertEqual(user_name, new_client.username)
        self.assertIsNone(new_client.password)
        self.assertEqual(new_client.management_url,
                         'http://admin:35357/v3')

    def test_trust_init(self):
        token = client_fixtures.trust_token()
        self.stub_auth(json=token)

        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            c = client.Client(user_domain_name=token.user_domain_name,
                              username=token.user_name,
                              password='password',
                              auth_url=self.TEST_URL,
                              trust_id=token.trust_id)
        self.assertIsNotNone(c.auth_ref)
        self.assertFalse(c.auth_ref.domain_scoped)
        self.assertFalse(c.auth_ref.project_scoped)
        self.assertEqual(token.trust_id, c.auth_ref.trust_id)
        self.assertEqual(token.trustee_user_id, c.auth_ref.trustee_user_id)
        self.assertEqual(token.trustor_user_id, c.auth_ref.trustor_user_id)
        self.assertTrue(c.auth_ref.trust_scoped)
        self.assertEqual(token.user_id, c.auth_user_id)

    def test_init_err_no_auth_url(self):
        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            self.assertRaises(exceptions.AuthorizationFailure,
                              client.Client,
                              username='exampleuser',
                              password='password')

    def _management_url_is_updated(self, fixture, **kwargs):
        second = copy.deepcopy(fixture)
        first_url = 'http://admin:35357/v3'
        second_url = "http://secondurl:%d/v3'"

        for entry in second['token']['catalog']:
            if entry['type'] == 'identity':
                entry['endpoints'] = [{
                    'url': second_url % 5000,
                    'region': 'RegionOne',
                    'interface': 'public'
                }, {
                    'url': second_url % 5000,
                    'region': 'RegionOne',
                    'interface': 'internal'
                }, {
                    'url': second_url % 35357,
                    'region': 'RegionOne',
                    'interface': 'admin'
                }]

        self.stub_auth(response_list=[{'json': fixture}, {'json': second}])

        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            cl = client.Client(username='exampleuser',
                               password='password',
                               auth_url=self.TEST_URL,
                               **kwargs)
        self.assertEqual(cl.management_url, first_url)

        with self.deprecations.expect_deprecations_here():
            cl.authenticate()
        self.assertEqual(cl.management_url, second_url % 35357)

    def test_management_url_is_updated_with_project(self):
        self._management_url_is_updated(client_fixtures.project_scoped_token(),
                                        project_name='exampleproject')

    def test_management_url_is_updated_with_domain(self):
        self._management_url_is_updated(client_fixtures.domain_scoped_token(),
                                        domain_name='exampledomain')

    def test_client_with_region_name_passes_to_service_catalog(self):
        # NOTE(jamielennox): this is deprecated behaviour that should be
        # removed ASAP, however must remain compatible.
        self.deprecations.expect_deprecations()

        self.stub_auth(json=client_fixtures.auth_response_body())

        cl = client.Client(username='exampleuser',
                           password='password',
                           project_name='exampleproject',
                           auth_url=self.TEST_URL,
                           region_name='North')
        self.assertEqual(cl.service_catalog.url_for(service_type='image'),
                         'http://glance.north.host/glanceapi/public')

        cl = client.Client(username='exampleuser',
                           password='password',
                           project_name='exampleproject',
                           auth_url=self.TEST_URL,
                           region_name='South')
        self.assertEqual(cl.service_catalog.url_for(service_type='image'),
                         'http://glance.south.host/glanceapi/public')

    def test_client_without_auth_params(self):
        # Creating a HTTPClient not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            self.assertRaises(exceptions.AuthorizationFailure,
                              client.Client,
                              project_name='exampleproject',
                              auth_url=self.TEST_URL)

    def test_client_params(self):
        with self.deprecations.expect_deprecations_here():
            sess = session.Session()
            auth = token_endpoint.Token('a', 'b')

        opts = {'auth': auth,
                'connect_retries': 50,
                'endpoint_override': uuid.uuid4().hex,
                'interface': uuid.uuid4().hex,
                'region_name': uuid.uuid4().hex,
                'service_name': uuid.uuid4().hex,
                'user_agent': uuid.uuid4().hex,
                }

        cl = client.Client(session=sess, **opts)

        for k, v in opts.items():
            self.assertEqual(v, getattr(cl._adapter, k))

        self.assertEqual('identity', cl._adapter.service_type)
        self.assertEqual((3, 0), cl._adapter.version)

    def test_empty_service_catalog_param(self):
        # Client().service_catalog should return None if the client is not
        # authenticated
        sess = auth_session.Session()
        cl = client.Client(session=sess)
        self.assertIsNone(cl.service_catalog)
