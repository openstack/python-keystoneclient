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
import json

import httpretty

from keystoneclient import exceptions
from keystoneclient.tests.v3 import client_fixtures
from keystoneclient.tests.v3 import utils
from keystoneclient.v3 import client


class KeystoneClientTest(utils.TestCase):

    @httpretty.activate
    def test_unscoped_init(self):
        self.stub_auth(json=client_fixtures.unscoped_token())

        c = client.Client(user_domain_name='exampledomain',
                          username='exampleuser',
                          password='password',
                          auth_url=self.TEST_URL)
        self.assertIsNotNone(c.auth_ref)
        self.assertFalse(c.auth_ref.domain_scoped)
        self.assertFalse(c.auth_ref.project_scoped)
        self.assertEqual(c.auth_user_id,
                         'c4da488862bd435c9e6c0275a0d0e49a')

    @httpretty.activate
    def test_domain_scoped_init(self):
        self.stub_auth(json=client_fixtures.domain_scoped_token())

        c = client.Client(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                          password='password',
                          domain_name='exampledomain',
                          auth_url=self.TEST_URL)
        self.assertIsNotNone(c.auth_ref)
        self.assertTrue(c.auth_ref.domain_scoped)
        self.assertFalse(c.auth_ref.project_scoped)
        self.assertEqual(c.auth_user_id,
                         'c4da488862bd435c9e6c0275a0d0e49a')
        self.assertEqual(c.auth_domain_id,
                         '8e9283b7ba0b1038840c3842058b86ab')

    @httpretty.activate
    def test_project_scoped_init(self):
        self.stub_auth(json=client_fixtures.project_scoped_token()),

        c = client.Client(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                          password='password',
                          user_domain_name='exampledomain',
                          project_name='exampleproject',
                          auth_url=self.TEST_URL)
        self.assertIsNotNone(c.auth_ref)
        self.assertFalse(c.auth_ref.domain_scoped)
        self.assertTrue(c.auth_ref.project_scoped)
        self.assertEqual(c.auth_user_id,
                         'c4da488862bd435c9e6c0275a0d0e49a')
        self.assertEqual(c.auth_tenant_id,
                         '225da22d3ce34b15877ea70b2a575f58')

    @httpretty.activate
    def test_auth_ref_load(self):
        self.stub_auth(json=client_fixtures.project_scoped_token())

        c = client.Client(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                          password='password',
                          project_id='225da22d3ce34b15877ea70b2a575f58',
                          auth_url=self.TEST_URL)
        cache = json.dumps(c.auth_ref)
        new_client = client.Client(auth_ref=json.loads(cache))
        self.assertIsNotNone(new_client.auth_ref)
        self.assertFalse(new_client.auth_ref.domain_scoped)
        self.assertTrue(new_client.auth_ref.project_scoped)
        self.assertEqual(new_client.username, 'exampleuser')
        self.assertIsNone(new_client.password)
        self.assertEqual(new_client.management_url,
                         'http://admin:35357/v3')

    @httpretty.activate
    def test_auth_ref_load_with_overridden_arguments(self):
        new_auth_url = 'https://newkeystone.com/v3'

        self.stub_auth(json=client_fixtures.project_scoped_token())
        self.stub_auth(json=client_fixtures.project_scoped_token(),
                       base_url=new_auth_url)

        c = client.Client(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                          password='password',
                          project_id='225da22d3ce34b15877ea70b2a575f58',
                          auth_url=self.TEST_URL)
        cache = json.dumps(c.auth_ref)
        new_client = client.Client(auth_ref=json.loads(cache),
                                   auth_url=new_auth_url)
        self.assertIsNotNone(new_client.auth_ref)
        self.assertFalse(new_client.auth_ref.domain_scoped)
        self.assertTrue(new_client.auth_ref.project_scoped)
        self.assertEqual(new_client.auth_url, new_auth_url)
        self.assertEqual(new_client.username, 'exampleuser')
        self.assertIsNone(new_client.password)
        self.assertEqual(new_client.management_url,
                         'http://admin:35357/v3')

    @httpretty.activate
    def test_trust_init(self):
        self.stub_auth(json=client_fixtures.trust_token())

        c = client.Client(user_domain_name='exampledomain',
                          username='exampleuser',
                          password='password',
                          auth_url=self.TEST_URL,
                          trust_id='fe0aef')
        self.assertIsNotNone(c.auth_ref)
        self.assertFalse(c.auth_ref.domain_scoped)
        self.assertFalse(c.auth_ref.project_scoped)
        self.assertEqual(c.auth_ref.trust_id, 'fe0aef')
        self.assertTrue(c.auth_ref.trust_scoped)
        self.assertEqual(c.auth_user_id, '0ca8f6')

    def test_init_err_no_auth_url(self):
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

        self.stub_auth(json=fixture)
        cl = client.Client(username='exampleuser',
                           password='password',
                           auth_url=self.TEST_URL,
                           **kwargs)

        self.assertEqual(cl.management_url, first_url)

        self.stub_auth(json=second)
        cl.authenticate()
        self.assertEqual(cl.management_url, second_url % 35357)

    @httpretty.activate
    def test_management_url_is_updated_with_project(self):
        self._management_url_is_updated(client_fixtures.project_scoped_token(),
                                        project_name='exampleproject')

    @httpretty.activate
    def test_management_url_is_updated_with_domain(self):
        self._management_url_is_updated(client_fixtures.domain_scoped_token(),
                                        domain_name='exampledomain')

    @httpretty.activate
    def test_client_with_region_name_passes_to_service_catalog(self):
        # NOTE(jamielennox): this is deprecated behaviour that should be
        # removed ASAP, however must remain compatible.

        self.stub_auth(json=client_fixtures.auth_response_body())

        cl = client.Client(username='exampleuser',
                           password='password',
                           tenant_name='exampleproject',
                           auth_url=self.TEST_URL,
                           region_name='North')
        self.assertEqual(cl.service_catalog.url_for(service_type='image'),
                         'http://glance.north.host/glanceapi/public')

        cl = client.Client(username='exampleuser',
                           password='password',
                           tenant_name='exampleproject',
                           auth_url=self.TEST_URL,
                           region_name='South')
        self.assertEqual(cl.service_catalog.url_for(service_type='image'),
                         'http://glance.south.host/glanceapi/public')
