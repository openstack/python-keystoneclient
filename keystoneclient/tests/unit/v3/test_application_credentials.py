# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid

from oslo_utils import timeutils

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import application_credentials


class ApplicationCredentialTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(ApplicationCredentialTests, self).setUp()
        self.key = 'application_credential'
        self.collection_key = 'application_credentials'
        self.model = application_credentials.ApplicationCredential
        self.manager = self.client.application_credentials
        self.path_prefix = 'users/%s' % self.TEST_USER_ID

    def new_ref(self, **kwargs):
        kwargs = super(ApplicationCredentialTests, self).new_ref(**kwargs)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('description', uuid.uuid4().hex)
        kwargs.setdefault('unrestricted', False)
        return kwargs

    def test_create_with_roles(self):
        ref = self.new_ref(user=uuid.uuid4().hex)
        ref['roles'] = [{'name': 'atestrole'}]
        req_ref = ref.copy()
        req_ref.pop('id')
        user = req_ref.pop('user')

        self.stub_entity('POST',
                         ['users', user, self.collection_key],
                         status_code=201, entity=req_ref)

        super(ApplicationCredentialTests, self).test_create(ref=ref,
                                                            req_ref=req_ref)

    def test_create_with_role_id_and_names(self):
        ref = self.new_ref(user=uuid.uuid4().hex)
        ref['roles'] = [{'name': 'atestrole', 'domain': 'nondefault'},
                        uuid.uuid4().hex]
        req_ref = ref.copy()
        req_ref.pop('id')
        user = req_ref.pop('user')

        req_ref['roles'] = [{'name': 'atestrole', 'domain': 'nondefault'},
                            {'id': ref['roles'][1]}]
        self.stub_entity('POST',
                         ['users', user, self.collection_key],
                         status_code=201, entity=req_ref)

        super(ApplicationCredentialTests, self).test_create(ref=ref,
                                                            req_ref=req_ref)

    def test_create_expires(self):
        ref = self.new_ref(user=uuid.uuid4().hex)
        ref['expires_at'] = timeutils.parse_isotime(
            '2013-03-04T12:00:01.000000Z')
        req_ref = ref.copy()
        req_ref.pop('id')
        user = req_ref.pop('user')

        req_ref['expires_at'] = '2013-03-04T12:00:01.000000Z'

        self.stub_entity('POST',
                         ['users', user, self.collection_key],
                         status_code=201, entity=req_ref)

        super(ApplicationCredentialTests, self).test_create(ref=ref,
                                                            req_ref=req_ref)

    def test_create_unrestricted(self):
        ref = self.new_ref(user=uuid.uuid4().hex)
        ref['unrestricted'] = True
        req_ref = ref.copy()
        req_ref.pop('id')
        user = req_ref.pop('user')

        self.stub_entity('POST',
                         ['users', user, self.collection_key],
                         status_code=201, entity=req_ref)

        super(ApplicationCredentialTests, self).test_create(ref=ref,
                                                            req_ref=req_ref)

    def test_get(self):
        ref = self.new_ref(user=uuid.uuid4().hex)

        self.stub_entity(
            'GET', ['users', ref['user'], self.collection_key, ref['id']],
            entity=ref)
        returned = self.manager.get(ref['id'], ref['user'])
        self.assertIsInstance(returned, self.model)
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_update(self):
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.update)
