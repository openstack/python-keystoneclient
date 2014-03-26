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

import uuid

import httpretty

from keystoneclient.tests.v3 import utils
from keystoneclient.v3.contrib.federation import identity_providers


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

    @httpretty.activate
    def test_create(self, ref=None, req_ref=None):
        ref = ref or self.new_ref()

        # req_ref argument allows you to specify a different
        # signature for the request when the manager does some
        # conversion before doing the request (e.g converting
        # from datetime object to timestamp string)
        req_ref = (req_ref or ref).copy()
        req_ref.pop('id')

        self.stub_entity(httpretty.PUT, entity=ref, id=ref['id'], status=201)

        returned = self.manager.create(**ref)
        self.assertIsInstance(returned, self.model)
        for attr in req_ref:
            self.assertEqual(
                getattr(returned, attr),
                req_ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)
