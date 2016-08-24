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

import copy
import uuid

from keystoneauth1 import fixture
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneauth1.tests.unit import k2k_fixtures
import six
from testtools import matchers

from keystoneclient import access
from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import client
from keystoneclient.v3.contrib.federation import base
from keystoneclient.v3.contrib.federation import identity_providers
from keystoneclient.v3.contrib.federation import mappings
from keystoneclient.v3.contrib.federation import protocols
from keystoneclient.v3.contrib.federation import service_providers
from keystoneclient.v3 import domains
from keystoneclient.v3 import projects


class IdentityProviderTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(IdentityProviderTests, self).setUp()
        self.key = 'identity_provider'
        self.collection_key = 'identity_providers'
        self.model = identity_providers.IdentityProvider
        self.manager = self.client.federation.identity_providers
        self.path_prefix = 'OS-FEDERATION'

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('description', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        return kwargs

    def test_positional_parameters_expect_fail(self):
        """Ensure CrudManager raises TypeError exceptions.

        After passing wrong number of positional arguments
        an exception should be raised.

        Operations to be tested:
            * create()
            * get()
            * list()
            * delete()
            * update()

        """
        POS_PARAM_1 = uuid.uuid4().hex
        POS_PARAM_2 = uuid.uuid4().hex
        POS_PARAM_3 = uuid.uuid4().hex

        PARAMETERS = {
            'create': (POS_PARAM_1, POS_PARAM_2),
            'get': (POS_PARAM_1, POS_PARAM_2),
            'list': (POS_PARAM_1, POS_PARAM_2),
            'update': (POS_PARAM_1, POS_PARAM_2, POS_PARAM_3),
            'delete': (POS_PARAM_1, POS_PARAM_2)
        }

        for f_name, args in PARAMETERS.items():
            self.assertRaises(TypeError, getattr(self.manager, f_name),
                              *args)

    def test_create(self):
        ref = self.new_ref()
        req_ref = ref.copy()
        req_ref.pop('id')

        self.stub_entity('PUT', entity=ref, id=ref['id'], status_code=201)

        returned = self.manager.create(**ref)
        self.assertIsInstance(returned, self.model)
        for attr in req_ref:
            self.assertEqual(
                getattr(returned, attr),
                req_ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)


class MappingTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(MappingTests, self).setUp()
        self.key = 'mapping'
        self.collection_key = 'mappings'
        self.model = mappings.Mapping
        self.manager = self.client.federation.mappings
        self.path_prefix = 'OS-FEDERATION'

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('rules', [uuid.uuid4().hex,
                                    uuid.uuid4().hex])
        return kwargs

    def test_create(self):
        ref = self.new_ref()
        manager_ref = ref.copy()
        mapping_id = manager_ref.pop('id')
        req_ref = ref.copy()

        self.stub_entity('PUT', entity=req_ref, id=mapping_id,
                         status_code=201)

        returned = self.manager.create(mapping_id=mapping_id, **manager_ref)
        self.assertIsInstance(returned, self.model)
        for attr in req_ref:
            self.assertEqual(
                getattr(returned, attr),
                req_ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(manager_ref)


class ProtocolTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(ProtocolTests, self).setUp()
        self.key = 'protocol'
        self.collection_key = 'protocols'
        self.model = protocols.Protocol
        self.manager = self.client.federation.protocols
        self.path_prefix = 'OS-FEDERATION/identity_providers'

    def _transform_to_response(self, ref):
        """Construct a response body from a dictionary."""
        response = copy.deepcopy(ref)
        del response['identity_provider']
        return response

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('mapping_id', uuid.uuid4().hex)
        kwargs.setdefault('identity_provider', uuid.uuid4().hex)
        return kwargs

    def build_parts(self, idp_id, protocol_id=None):
        """Build array used to construct mocking URL.

        Construct and return array with URL parts later used
        by methods like utils.TestCase.stub_entity().
        Example of URL:
        ``OS-FEDERATION/identity_providers/{idp_id}/
        protocols/{protocol_id}``

        """
        parts = ['OS-FEDERATION', 'identity_providers',
                 idp_id, 'protocols']
        if protocol_id:
            parts.append(protocol_id)
        return parts

    def test_build_url_provide_base_url(self):
        base_url = uuid.uuid4().hex
        parameters = {'base_url': base_url}
        url = self.manager.build_url(dict_args_in_out=parameters)
        self.assertEqual('/'.join([base_url, self.collection_key]), url)

    def test_build_url_w_idp_id(self):
        """Test whether kwargs ``base_url`` discards object's base_url.

        This test shows, that when ``base_url`` is specified in the
        dict_args_in_out dictionary,  values like ``identity_provider_id``
        are not taken into consideration while building the url.

        """
        base_url, identity_provider_id = uuid.uuid4().hex, uuid.uuid4().hex
        parameters = {
            'base_url': base_url,
            'identity_provider_id': identity_provider_id
        }
        url = self.manager.build_url(dict_args_in_out=parameters)
        self.assertEqual('/'.join([base_url, self.collection_key]), url)

    def test_build_url_default_base_url(self):
        identity_provider_id = uuid.uuid4().hex
        parameters = {
            'identity_provider_id': identity_provider_id
        }

        url = self.manager.build_url(dict_args_in_out=parameters)
        self.assertEqual(
            '/'.join([self.manager.base_url, identity_provider_id,
                      self.manager.collection_key]), url)

    def test_create(self):
        """Test creating federation protocol tied to an Identity Provider.

        URL to be tested: PUT /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        """
        ref = self.new_ref()
        expected = self._transform_to_response(ref)
        parts = self.build_parts(
            idp_id=ref['identity_provider'],
            protocol_id=ref['id'])
        self.stub_entity('PUT', entity=expected,
                         parts=parts, status_code=201)
        returned = self.manager.create(
            protocol_id=ref['id'],
            identity_provider=ref['identity_provider'],
            mapping=ref['mapping_id'])
        self.assertEqual(expected, returned.to_dict())
        request_body = {'mapping_id': ref['mapping_id']}
        self.assertEntityRequestBodyIs(request_body)

    def test_get(self):
        """Fetch federation protocol object.

        URL to be tested: GET /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        """
        ref = self.new_ref()
        expected = self._transform_to_response(ref)

        parts = self.build_parts(
            idp_id=ref['identity_provider'],
            protocol_id=ref['id'])
        self.stub_entity('GET', entity=expected,
                         parts=parts, status_code=201)

        returned = self.manager.get(ref['identity_provider'],
                                    ref['id'])
        self.assertIsInstance(returned, self.model)
        self.assertEqual(expected, returned.to_dict())

    def test_delete(self):
        """Delete federation protocol object.

        URL to be tested: DELETE /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        """
        ref = self.new_ref()
        parts = self.build_parts(
            idp_id=ref['identity_provider'],
            protocol_id=ref['id'])

        self.stub_entity('DELETE', parts=parts, status_code=204)

        self.manager.delete(ref['identity_provider'],
                            ref['id'])

    def test_list(self):
        """Test listing all federation protocols tied to the Identity Provider.

        URL to be tested: GET /OS-FEDERATION/identity_providers/
        $identity_provider/protocols

        """
        def _ref_protocols():
            return {
                'id': uuid.uuid4().hex,
                'mapping_id': uuid.uuid4().hex
            }

        ref = self.new_ref()
        expected = [_ref_protocols() for _ in range(3)]
        parts = self.build_parts(idp_id=ref['identity_provider'])
        self.stub_entity('GET', parts=parts,
                         entity=expected, status_code=200)

        returned = self.manager.list(ref['identity_provider'])
        for obj, ref_obj in zip(returned, expected):
            self.assertEqual(obj.to_dict(), ref_obj)

    def test_list_by_id(self):
        # The test in the parent class needs to be overridden because it
        # assumes globally unique IDs, which is not the case with protocol IDs
        # (which are contextualized per identity provider).
        ref = self.new_ref()
        super(ProtocolTests, self).test_list_by_id(
            ref=ref,
            identity_provider=ref['identity_provider'],
            id=ref['id'])

    def test_list_params(self):
        request_args = self.new_ref()
        filter_kwargs = {uuid.uuid4().hex: uuid.uuid4().hex}
        parts = self.build_parts(request_args['identity_provider'])

        # Return HTTP 401 as we don't accept such requests.
        self.stub_entity('GET', parts=parts, status_code=401)
        self.assertRaises(exceptions.Unauthorized,
                          self.manager.list,
                          request_args['identity_provider'],
                          **filter_kwargs)
        self.assertQueryStringContains(**filter_kwargs)

    def test_update(self):
        """Test updating federation protocol.

        URL to be tested: PATCH /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        """
        ref = self.new_ref()
        expected = self._transform_to_response(ref)

        parts = self.build_parts(
            idp_id=ref['identity_provider'],
            protocol_id=ref['id'])

        self.stub_entity('PATCH', parts=parts,
                         entity=expected, status_code=200)

        returned = self.manager.update(ref['identity_provider'],
                                       ref['id'],
                                       mapping=ref['mapping_id'])
        self.assertIsInstance(returned, self.model)
        self.assertEqual(expected, returned.to_dict())
        request_body = {'mapping_id': ref['mapping_id']}
        self.assertEntityRequestBodyIs(request_body)


class EntityManagerTests(utils.ClientTestCase):
    def test_create_object_expect_fail(self):
        self.assertRaises(TypeError,
                          base.EntityManager,
                          self.client)


class FederationProjectTests(utils.ClientTestCase):

    def setUp(self):
        super(FederationProjectTests, self).setUp()
        self.key = 'project'
        self.collection_key = 'projects'
        self.model = projects.Project
        self.manager = self.client.federation.projects
        self.URL = "%s%s" % (self.TEST_URL, '/auth/projects')

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('domain_id', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs

    def test_list_accessible_projects(self):
        projects_ref = [self.new_ref(), self.new_ref()]
        projects_json = {
            self.collection_key: [self.new_ref(), self.new_ref()]
        }
        self.requests_mock.get(self.URL, json=projects_json)
        returned_list = self.manager.list()

        self.assertEqual(len(projects_ref), len(returned_list))
        for project in returned_list:
            self.assertIsInstance(project, self.model)


class K2KFederatedProjectTests(utils.TestCase):

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v3')
    TEST_PASS = 'password'
    REQUEST_ECP_URL = TEST_URL + '/auth/OS-FEDERATION/saml2/ecp'

    SP_ID = 'sp1'
    SP_ROOT_URL = 'https://example.com/v3'
    SP_URL = 'https://example.com/Shibboleth.sso/SAML2/ECP'
    SP_AUTH_URL = (SP_ROOT_URL +
                   '/OS-FEDERATION/identity_providers'
                   '/testidp/protocols/saml2/auth')

    def setUp(self):
        super(K2KFederatedProjectTests, self).setUp()
        self.token_v3 = fixture.V3Token()
        self.token_v3.add_service_provider(
            self.SP_ID, self.SP_AUTH_URL, self.SP_URL)
        self.session = session.Session()
        self.collection_key = 'projects'
        self.model = projects.Project
        self.URL = '%s%s' % (self.SP_ROOT_URL, '/auth/projects')
        self.k2kplugin = self.get_plugin()
        self._mock_k2k_flow_urls()

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('domain_id', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs

    def _get_base_plugin(self):
        self.stub_url('POST', ['auth', 'tokens'],
                      headers={'X-Subject-Token': uuid.uuid4().hex},
                      json=self.token_v3)
        return v3.Password(self.TEST_URL,
                           username=self.TEST_USER,
                           password=self.TEST_PASS)

    def _mock_k2k_flow_urls(self):
        # We need to check the auth versions available
        self.requests_mock.get(
            self.TEST_URL,
            json={'version': fixture.V3Discovery(self.TEST_URL)},
            headers={'Content-Type': 'application/json'})

        # The identity provider receives a request for an ECP wrapped
        # assertion. This assertion contains the user authentication info
        # and will be presented to the service provider
        self.requests_mock.register_uri(
            'POST',
            self.REQUEST_ECP_URL,
            content=six.b(k2k_fixtures.ECP_ENVELOPE),
            headers={'Content-Type': 'application/vnd.paos+xml'},
            status_code=200)

        # The service provider is presented with the ECP wrapped assertion
        # generated by the identity provider and should return a redirect
        # (302 or 303) upon successful authentication
        self.requests_mock.register_uri(
            'POST',
            self.SP_URL,
            content=six.b(k2k_fixtures.TOKEN_BASED_ECP),
            headers={'Content-Type': 'application/vnd.paos+xml'},
            status_code=302)

        # Should not follow the redirect URL, but use the auth_url attribute
        self.requests_mock.register_uri(
            'GET',
            self.SP_AUTH_URL,
            json=k2k_fixtures.UNSCOPED_TOKEN,
            headers={'X-Subject-Token': k2k_fixtures.UNSCOPED_TOKEN_HEADER})

    def get_plugin(self, **kwargs):
        kwargs.setdefault('base_plugin', self._get_base_plugin())
        kwargs.setdefault('service_provider', self.SP_ID)
        return v3.Keystone2Keystone(**kwargs)

    def test_list_projects(self):
        k2k_client = client.Client(session=self.session, auth=self.k2kplugin)
        self.requests_mock.get(self.URL, json={
            self.collection_key: [self.new_ref(), self.new_ref()]
        })
        self.requests_mock.get(self.SP_ROOT_URL, json={
            'version': fixture.discovery.V3Discovery(self.SP_ROOT_URL)
        })
        returned_list = k2k_client.federation.projects.list()

        self.assertThat(returned_list, matchers.HasLength(2))
        for project in returned_list:
            self.assertIsInstance(project, self.model)


class FederationDomainTests(utils.ClientTestCase):

    def setUp(self):
        super(FederationDomainTests, self).setUp()
        self.key = 'domain'
        self.collection_key = 'domains'
        self.model = domains.Domain
        self.manager = self.client.federation.domains

        self.URL = "%s%s" % (self.TEST_URL, '/auth/domains')

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('description', uuid.uuid4().hex)
        return kwargs

    def test_list_accessible_domains(self):
        domains_ref = [self.new_ref(), self.new_ref()]
        domains_json = {
            self.collection_key: domains_ref
        }
        self.requests_mock.get(self.URL, json=domains_json)
        returned_list = self.manager.list()
        self.assertEqual(len(domains_ref), len(returned_list))
        for domain in returned_list:
            self.assertIsInstance(domain, self.model)


class FederatedTokenTests(utils.ClientTestCase):

    def setUp(self):
        super(FederatedTokenTests, self).setUp()
        token = fixture.V3FederationToken()
        token.set_project_scope()
        token.add_role()
        self.federated_token = access.AccessInfo.factory(body=token)

    def test_federated_property_federated_token(self):
        """Check if is_federated property returns expected value."""
        self.assertTrue(self.federated_token.is_federated)

    def test_get_user_domain_name(self):
        """Ensure a federated user's domain name does not exist."""
        self.assertIsNone(self.federated_token.user_domain_name)

    def test_get_user_domain_id(self):
        """Ensure a federated user's domain ID does not exist."""
        self.assertEqual('Federated', self.federated_token.user_domain_id)


class ServiceProviderTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(ServiceProviderTests, self).setUp()
        self.key = 'service_provider'
        self.collection_key = 'service_providers'
        self.model = service_providers.ServiceProvider
        self.manager = self.client.federation.service_providers
        self.path_prefix = 'OS-FEDERATION'

    def new_ref(self, **kwargs):
        kwargs.setdefault('auth_url', uuid.uuid4().hex)
        kwargs.setdefault('description', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('sp_url', uuid.uuid4().hex)
        return kwargs

    def test_positional_parameters_expect_fail(self):
        """Ensure CrudManager raises TypeError exceptions.

        After passing wrong number of positional arguments
        an exception should be raised.

        Operations to be tested:
            * create()
            * get()
            * list()
            * delete()
            * update()

        """
        POS_PARAM_1 = uuid.uuid4().hex
        POS_PARAM_2 = uuid.uuid4().hex
        POS_PARAM_3 = uuid.uuid4().hex

        PARAMETERS = {
            'create': (POS_PARAM_1, POS_PARAM_2),
            'get': (POS_PARAM_1, POS_PARAM_2),
            'list': (POS_PARAM_1, POS_PARAM_2),
            'update': (POS_PARAM_1, POS_PARAM_2, POS_PARAM_3),
            'delete': (POS_PARAM_1, POS_PARAM_2)
        }

        for f_name, args in PARAMETERS.items():
            self.assertRaises(TypeError, getattr(self.manager, f_name),
                              *args)

    def test_create(self):
        ref = self.new_ref()

        # req_ref argument allows you to specify a different
        # signature for the request when the manager does some
        # conversion before doing the request (e.g. converting
        # from datetime object to timestamp string)
        req_ref = ref.copy()
        req_ref.pop('id')

        self.stub_entity('PUT', entity=ref, id=ref['id'], status_code=201)

        returned = self.manager.create(**ref)
        self.assertIsInstance(returned, self.model)
        for attr in req_ref:
            self.assertEqual(
                getattr(returned, attr),
                req_ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)
