# Copyright 2012 OpenStack Foundation
#
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

import mock
import uuid

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import users


class UserTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(UserTests, self).setUp()
        self.key = 'user'
        self.collection_key = 'users'
        self.model = users.User
        self.manager = self.client.users

    def new_ref(self, **kwargs):
        kwargs = super(UserTests, self).new_ref(**kwargs)
        kwargs.setdefault('description', uuid.uuid4().hex)
        kwargs.setdefault('domain_id', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('default_project_id', uuid.uuid4().hex)
        return kwargs

    def test_add_user_to_group(self):
        group_id = uuid.uuid4().hex
        ref = self.new_ref()
        self.stub_url('PUT',
                      ['groups', group_id, self.collection_key, ref['id']],
                      status_code=204)

        self.manager.add_to_group(user=ref['id'], group=group_id)
        self.assertRaises(exceptions.ValidationError,
                          self.manager.remove_from_group,
                          user=ref['id'],
                          group=None)

    def test_list_users_in_group(self):
        group_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['groups', group_id, self.collection_key],
                         entity=ref_list)

        returned_list = self.manager.list(group=group_id)
        self.assertEqual(len(ref_list), len(returned_list))
        [self.assertIsInstance(r, self.model) for r in returned_list]

    def test_check_user_in_group(self):
        group_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['groups', group_id, self.collection_key, ref['id']],
                      status_code=204)

        self.manager.check_in_group(user=ref['id'], group=group_id)

        self.assertRaises(exceptions.ValidationError,
                          self.manager.check_in_group,
                          user=ref['id'],
                          group=None)

    def test_remove_user_from_group(self):
        group_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['groups', group_id, self.collection_key, ref['id']],
                      status_code=204)

        self.manager.remove_from_group(user=ref['id'], group=group_id)
        self.assertRaises(exceptions.ValidationError,
                          self.manager.remove_from_group,
                          user=ref['id'],
                          group=None)

    def test_create_doesnt_log_password(self):
        password = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_entity('POST', [self.collection_key],
                         status_code=201, entity=ref)

        req_ref = ref.copy()
        req_ref.pop('id')
        param_ref = req_ref.copy()

        param_ref['password'] = password
        params = utils.parameterize(param_ref)

        self.manager.create(**params)

        self.assertNotIn(password, self.logger.output)

    def test_create_with_project(self):
        # Can create a user with the deprecated project option rather than
        # default_project_id.
        self.deprecations.expect_deprecations()
        ref = self.new_ref()

        self.stub_entity('POST', [self.collection_key],
                         status_code=201, entity=ref)

        req_ref = ref.copy()
        req_ref.pop('id')
        param_ref = req_ref.copy()
        # Use deprecated project_id rather than new default_project_id.
        param_ref['project_id'] = param_ref.pop('default_project_id')
        params = utils.parameterize(param_ref)

        returned = self.manager.create(**params)
        self.assertIsInstance(returned, self.model)
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)

    def test_create_with_project_and_default_project(self):
        # Can create a user with the deprecated project and default_project_id.
        # The backend call should only pass the default_project_id.
        self.deprecations.expect_deprecations()

        ref = self.new_ref()

        self.stub_entity('POST',
                         [self.collection_key],
                         status_code=201, entity=ref)

        req_ref = ref.copy()
        req_ref.pop('id')
        param_ref = req_ref.copy()

        # Add the deprecated project_id in the call, the value will be ignored.
        param_ref['project_id'] = 'project'
        params = utils.parameterize(param_ref)

        returned = self.manager.create(**params)
        self.assertIsInstance(returned, self.model)
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)

    def test_update_doesnt_log_password(self):
        password = uuid.uuid4().hex
        ref = self.new_ref()

        req_ref = ref.copy()
        req_ref.pop('id')
        param_ref = req_ref.copy()

        self.stub_entity('PATCH',
                         [self.collection_key, ref['id']],
                         status_code=200, entity=ref)

        param_ref['password'] = password
        params = utils.parameterize(param_ref)

        self.manager.update(ref['id'], **params)

        self.assertNotIn(password, self.logger.output)

    def test_update_with_project(self):
        # Can update a user with the deprecated project option rather than
        # default_project_id.
        self.deprecations.expect_deprecations()

        ref = self.new_ref()
        req_ref = ref.copy()
        req_ref.pop('id')
        param_ref = req_ref.copy()

        self.stub_entity('PATCH',
                         [self.collection_key, ref['id']],
                         status_code=200, entity=ref)

        # Use deprecated project_id rather than new default_project_id.
        param_ref['project_id'] = param_ref.pop('default_project_id')
        params = utils.parameterize(param_ref)

        returned = self.manager.update(ref['id'], **params)
        self.assertIsInstance(returned, self.model)
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)

    def test_update_with_project_and_default_project(self, ref=None):
        self.deprecations.expect_deprecations()

        ref = self.new_ref()
        req_ref = ref.copy()
        req_ref.pop('id')
        param_ref = req_ref.copy()

        self.stub_entity('PATCH',
                         [self.collection_key, ref['id']],
                         status_code=200, entity=ref)

        # Add the deprecated project_id in the call, the value will be ignored.
        param_ref['project_id'] = 'project'
        params = utils.parameterize(param_ref)

        returned = self.manager.update(ref['id'], **params)
        self.assertIsInstance(returned, self.model)
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)

    def test_update_password(self):
        old_password = uuid.uuid4().hex
        new_password = uuid.uuid4().hex

        self.stub_url('POST',
                      [self.collection_key, self.TEST_USER_ID, 'password'])
        self.client.user_id = self.TEST_USER_ID
        self.manager.update_password(old_password, new_password)

        exp_req_body = {
            'user': {
                'password': new_password, 'original_password': old_password
            }
        }

        self.assertEqual(
            '%s/users/%s/password' % (self.TEST_URL, self.TEST_USER_ID),
            self.requests_mock.last_request.url)
        self.assertRequestBodyIs(json=exp_req_body)
        self.assertNotIn(old_password, self.logger.output)
        self.assertNotIn(new_password, self.logger.output)

    def test_update_password_with_no_hardcoded_endpoint_filter(self):
        # test to ensure the 'endpoint_filter' parameter is not being
        # passed from the manager. Endpoint filtering should be done at
        # the Session, not the individual managers.
        old_password = uuid.uuid4().hex
        new_password = uuid.uuid4().hex
        expected_params = {'user': {'password': new_password,
                                    'original_password': old_password}}
        user_password_update_path = '/users/%s/password' % self.TEST_USER_ID

        self.client.user_id = self.TEST_USER_ID
        # NOTE(gyee): user manager subclass keystoneclient.base.Manager
        # and utilize the _update() method in the base class to interface
        # with the client session to perform the update. In the case, we
        # just need to make sure the 'endpoint_filter' parameter is not
        # there.
        with mock.patch('keystoneclient.base.Manager._update') as m:
            self.manager.update_password(old_password, new_password)
            m.assert_called_with(user_password_update_path, expected_params,
                                 method='POST', log=False)

    def test_update_password_with_bad_inputs(self):
        old_password = uuid.uuid4().hex
        new_password = uuid.uuid4().hex

        # users can't unset their password
        self.assertRaises(exceptions.ValidationError,
                          self.manager.update_password,
                          old_password, None)
        self.assertRaises(exceptions.ValidationError,
                          self.manager.update_password,
                          old_password, '')

        # users can't start with empty passwords
        self.assertRaises(exceptions.ValidationError,
                          self.manager.update_password,
                          None, new_password)
        self.assertRaises(exceptions.ValidationError,
                          self.manager.update_password,
                          '', new_password)

        # this wouldn't result in any change anyway
        self.assertRaises(exceptions.ValidationError,
                          self.manager.update_password,
                          None, None)
        self.assertRaises(exceptions.ValidationError,
                          self.manager.update_password,
                          '', '')
        password = uuid.uuid4().hex
        self.assertRaises(exceptions.ValidationError,
                          self.manager.update_password,
                          password, password)
