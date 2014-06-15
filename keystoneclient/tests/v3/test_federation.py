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

from keystoneclient import exceptions
from keystoneclient.tests.v3 import utils
from keystoneclient.v3.contrib.federation import identity_providers
from keystoneclient.v3.contrib.federation import mappings
from keystoneclient.v3.contrib.federation import protocols


class IdentityProviderTests(utils.TestCase, utils.CrudTests):
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

    def test_create(self, ref=None, req_ref=None):
        ref = ref or self.new_ref()

        # req_ref argument allows you to specify a different
        # signature for the request when the manager does some
        # conversion before doing the request (e.g. converting
        # from datetime object to timestamp string)
        req_ref = (req_ref or ref).copy()
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


class MappingTests(utils.TestCase, utils.CrudTests):
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

    def test_create(self, ref=None, req_ref=None):
        ref = ref or self.new_ref()
        manager_ref = ref.copy()
        mapping_id = manager_ref.pop('id')

        # req_ref argument allows you to specify a different
        # signature for the request when the manager does some
        # conversion before doing the request (e.g. converting
        # from datetime object to timestamp string)
        req_ref = (req_ref or ref).copy()

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


class ProtocolTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(ProtocolTests, self).setUp()
        self.key = 'protocol'
        self.collection_key = 'protocols'
        self.model = protocols.Protocol
        self.manager = self.client.federation.protocols
        self.path_prefix = 'OS-FEDERATION/identity_providers'

    def _transform_to_response(self, ref):
        """Rebuild dictionary so it can be used as a
        reference response body.

        """
        response = copy.deepcopy(ref)
        response['id'] = response.pop('protocol_id')
        del response['identity_provider']
        return response

    def new_ref(self, **kwargs):
        kwargs.setdefault('mapping', uuid.uuid4().hex)
        kwargs.setdefault('identity_provider', uuid.uuid4().hex)
        kwargs.setdefault('protocol_id', uuid.uuid4().hex)
        return kwargs

    def build_parts(self, identity_provider, protocol_id=None):
        """Build array used to construct mocking URL.

        Construct and return array with URL parts later used
        by methods like utils.TestCase.stub_entity().
        Example of URL:
        ``OS-FEDERATION/identity_providers/{idp_id}/
        protocols/{protocol_id}``

        """
        parts = ['OS-FEDERATION', 'identity_providers',
                 identity_provider, 'protocols']
        if protocol_id:
            parts.append(protocol_id)
        return parts

    def test_build_url_provide_base_url(self):
        base_url = uuid.uuid4().hex
        parameters = {'base_url': base_url}
        url = self.manager.build_url(dict_args_in_out=parameters)
        self.assertEqual('/'.join([base_url, self.collection_key]), url)

    def test_build_url_w_idp_id(self):
        """Test whether kwargs ``base_url`` discards object's base_url

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
        request_args = self.new_ref()
        expected = self._transform_to_response(request_args)
        parts = self.build_parts(request_args['identity_provider'],
                                 request_args['protocol_id'])
        self.stub_entity('PUT', entity=expected,
                         parts=parts, status_code=201)
        returned = self.manager.create(**request_args)
        self.assertEqual(expected, returned.to_dict())
        request_body = {'mapping_id': request_args['mapping']}
        self.assertEntityRequestBodyIs(request_body)

    def test_get(self):
        """Fetch federation protocol object.

        URL to be tested: GET /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        """
        request_args = self.new_ref()
        expected = self._transform_to_response(request_args)

        parts = self.build_parts(request_args['identity_provider'],
                                 request_args['protocol_id'])
        self.stub_entity('GET', entity=expected,
                         parts=parts, status_code=201)

        returned = self.manager.get(request_args['identity_provider'],
                                    request_args['protocol_id'])
        self.assertIsInstance(returned, self.model)
        self.assertEqual(expected, returned.to_dict())

    def test_delete(self):
        """Delete federation protocol object.

        URL to be tested: DELETE /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        """
        request_args = self.new_ref()
        parts = self.build_parts(request_args['identity_provider'],
                                 request_args['protocol_id'])

        self.stub_entity('DELETE', parts=parts, status_code=204)

        self.manager.delete(request_args['identity_provider'],
                            request_args['protocol_id'])

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

        request_args = self.new_ref()
        expected = [_ref_protocols() for _ in range(3)]
        parts = self.build_parts(request_args['identity_provider'])
        self.stub_entity('GET', parts=parts,
                         entity=expected, status_code=200)

        returned = self.manager.list(request_args['identity_provider'])
        for obj, ref_obj in zip(returned, expected):
            self.assertEqual(obj.to_dict(), ref_obj)

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
        """Test updating federation protocol

        URL to be tested: PATCH /OS-FEDERATION/identity_providers/
        $identity_provider/protocols/$protocol

        """
        request_args = self.new_ref()
        expected = self._transform_to_response(request_args)

        parts = self.build_parts(request_args['identity_provider'],
                                 request_args['protocol_id'])

        self.stub_entity('PATCH', parts=parts,
                         entity=expected, status_code=200)

        returned = self.manager.update(request_args['identity_provider'],
                                       request_args['protocol_id'],
                                       mapping=request_args['mapping'])
        self.assertIsInstance(returned, self.model)
        self.assertEqual(expected, returned.to_dict())
        request_body = {'mapping_id': request_args['mapping']}
        self.assertEntityRequestBodyIs(request_body)
