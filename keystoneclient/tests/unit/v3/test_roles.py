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

import uuid

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import roles
from testtools import matchers


class RoleTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(RoleTests, self).setUp()
        self.key = 'role'
        self.collection_key = 'roles'
        self.model = roles.Role
        self.manager = self.client.roles

    def new_ref(self, **kwargs):
        kwargs = super(RoleTests, self).new_ref(**kwargs)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs

    def _new_domain_ref(self, **kwargs):
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs

    def test_create_with_domain_id(self):
        ref = self.new_ref()
        ref['domain_id'] = uuid.uuid4().hex
        self.test_create(ref=ref)

    def test_create_with_domain(self):
        ref = self.new_ref()
        domain_ref = self._new_domain_ref()
        domain_ref['id'] = uuid.uuid4().hex
        ref['domain_id'] = domain_ref['id']

        self.stub_entity('POST', entity=ref, status_code=201)
        returned = self.manager.create(name=ref['name'],
                                       domain=domain_ref)
        self.assertIsInstance(returned, self.model)
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_domain_role_grant(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('PUT',
                      ['domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status_code=201)

        self.manager.grant(role=ref['id'], domain=domain_id, user=user_id)

    def test_domain_role_grant_inherited(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('PUT',
                      ['OS-INHERIT', 'domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=201)

        self.manager.grant(role=ref['id'], domain=domain_id, user=user_id,
                           os_inherit_extension_inherited=True)

    def test_project_role_grant_inherited(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('PUT',
                      ['OS-INHERIT', 'projects', project_id, 'users', user_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.grant(role=ref['id'], project=project_id, user=user_id,
                           os_inherit_extension_inherited=True)

    def test_domain_group_role_grant(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('PUT',
                      ['domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status_code=201)

        self.manager.grant(role=ref['id'], domain=domain_id, group=group_id)

    def test_domain_group_role_grant_inherited(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('PUT',
                      ['OS-INHERIT', 'domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=201)

        self.manager.grant(role=ref['id'], domain=domain_id, group=group_id,
                           os_inherit_extension_inherited=True)

    def test_project_group_role_grant_inherited(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('PUT',
                      ['OS-INHERIT', 'projects', project_id, 'groups',
                       group_id, self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.grant(role=ref['id'], project=project_id, group=group_id,
                           os_inherit_extension_inherited=True)

    def test_domain_role_list(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['domains', domain_id, 'users', user_id,
                          self.collection_key], entity=ref_list)

        self.manager.list(domain=domain_id, user=user_id)

    def test_domain_role_list_inherited(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['OS-INHERIT',
                          'domains', domain_id, 'users', user_id,
                          self.collection_key, 'inherited_to_projects'],
                         entity=ref_list)

        returned_list = self.manager.list(domain=domain_id, user=user_id,
                                          os_inherit_extension_inherited=True)

        self.assertThat(ref_list, matchers.HasLength(len(returned_list)))
        [self.assertIsInstance(r, self.model) for r in returned_list]

    def test_project_user_role_list_inherited(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['OS-INHERIT',
                          'projects', project_id, 'users', user_id,
                          self.collection_key, 'inherited_to_projects'],
                         entity=ref_list)

        returned_list = self.manager.list(project=project_id, user=user_id,
                                          os_inherit_extension_inherited=True)

        self.assertThat(ref_list, matchers.HasLength(len(returned_list)))
        [self.assertIsInstance(r, self.model) for r in returned_list]

    def test_domain_group_role_list(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['domains', domain_id, 'groups', group_id,
                          self.collection_key], entity=ref_list)

        self.manager.list(domain=domain_id, group=group_id)

    def test_domain_group_role_list_inherited(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['OS-INHERIT',
                          'domains', domain_id, 'groups', group_id,
                          self.collection_key, 'inherited_to_projects'],
                         entity=ref_list)

        returned_list = self.manager.list(domain=domain_id, group=group_id,
                                          os_inherit_extension_inherited=True)

        self.assertThat(ref_list, matchers.HasLength(len(returned_list)))
        [self.assertIsInstance(r, self.model) for r in returned_list]

    def test_project_group_role_list_inherited(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['OS-INHERIT',
                          'projects', project_id, 'groups', group_id,
                          self.collection_key, 'inherited_to_projects'],
                         entity=ref_list)

        returned_list = self.manager.list(project=project_id, group=group_id,
                                          os_inherit_extension_inherited=True)

        self.assertThat(ref_list, matchers.HasLength(len(returned_list)))
        [self.assertIsInstance(r, self.model) for r in returned_list]

    def test_domain_role_check(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status_code=204)

        self.manager.check(role=ref['id'], domain=domain_id,
                           user=user_id)

    def test_domain_role_check_inherited(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['OS-INHERIT',
                       'domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.check(role=ref['id'], domain=domain_id,
                           user=user_id, os_inherit_extension_inherited=True)

    def test_project_role_check_inherited(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['OS-INHERIT',
                       'projects', project_id, 'users', user_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.check(role=ref['id'], project=project_id,
                           user=user_id, os_inherit_extension_inherited=True)

    def test_domain_group_role_check(self):
        return
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status_code=204)

        self.manager.check(role=ref['id'], domain=domain_id, group=group_id)

    def test_domain_group_role_check_inherited(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['OS-INHERIT',
                       'domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.check(role=ref['id'], domain=domain_id,
                           group=group_id, os_inherit_extension_inherited=True)

    def test_project_group_role_check_inherited(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['OS-INHERIT',
                       'projects', project_id, 'groups', group_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.check(role=ref['id'], project=project_id,
                           group=group_id, os_inherit_extension_inherited=True)

    def test_domain_role_revoke(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status_code=204)

        self.manager.revoke(role=ref['id'], domain=domain_id, user=user_id)

    def test_domain_group_role_revoke(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status_code=204)

        self.manager.revoke(role=ref['id'], domain=domain_id, group=group_id)

    def test_domain_role_revoke_inherited(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['OS-INHERIT', 'domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.revoke(role=ref['id'], domain=domain_id,
                            user=user_id, os_inherit_extension_inherited=True)

    def test_project_role_revoke_inherited(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['OS-INHERIT', 'projects', project_id, 'users', user_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.revoke(role=ref['id'], project=project_id,
                            user=user_id, os_inherit_extension_inherited=True)

    def test_domain_group_role_revoke_inherited(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['OS-INHERIT', 'domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=200)

        self.manager.revoke(role=ref['id'], domain=domain_id,
                            group=group_id,
                            os_inherit_extension_inherited=True)

    def test_project_group_role_revoke_inherited(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['OS-INHERIT', 'projects', project_id, 'groups',
                       group_id, self.collection_key, ref['id'],
                       'inherited_to_projects'],
                      status_code=204)

        self.manager.revoke(role=ref['id'], project=project_id,
                            group=group_id,
                            os_inherit_extension_inherited=True)

    def test_project_role_grant(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('PUT',
                      ['projects', project_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status_code=201)

        self.manager.grant(role=ref['id'], project=project_id, user=user_id)

    def test_project_group_role_grant(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('PUT',
                      ['projects', project_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status_code=201)

        self.manager.grant(role=ref['id'], project=project_id, group=group_id)

    def test_project_role_list(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['projects', project_id, 'users', user_id,
                          self.collection_key], entity=ref_list)

        self.manager.list(project=project_id, user=user_id)

    def test_project_group_role_list(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity('GET',
                         ['projects', project_id, 'groups', group_id,
                          self.collection_key], entity=ref_list)

        self.manager.list(project=project_id, group=group_id)

    def test_project_role_check(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['projects', project_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status_code=200)

        self.manager.check(role=ref['id'], project=project_id, user=user_id)

    def test_project_group_role_check(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('HEAD',
                      ['projects', project_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status_code=200)

        self.manager.check(role=ref['id'], project=project_id, group=group_id)

    def test_project_role_revoke(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['projects', project_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status_code=204)

        self.manager.revoke(role=ref['id'], project=project_id, user=user_id)

    def test_project_group_role_revoke(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url('DELETE',
                      ['projects', project_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status_code=204)

        self.manager.revoke(role=ref['id'], project=project_id, group=group_id)

    def test_domain_project_role_grant_fails(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.grant,
            role=ref['id'],
            domain=domain_id,
            project=project_id,
            user=user_id)

    def test_domain_project_role_list_fails(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.list,
            domain=domain_id,
            project=project_id,
            user=user_id)

    def test_domain_project_role_check_fails(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.check,
            role=ref['id'],
            domain=domain_id,
            project=project_id,
            user=user_id)

    def test_domain_project_role_revoke_fails(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.revoke,
            role=ref['id'],
            domain=domain_id,
            project=project_id,
            user=user_id)

    def test_user_group_role_grant_fails(self):
        user_id = uuid.uuid4().hex
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.grant,
            role=ref['id'],
            project=project_id,
            group=group_id,
            user=user_id)

    def test_user_group_role_list_fails(self):
        user_id = uuid.uuid4().hex
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.list,
            project=project_id,
            group=group_id,
            user=user_id)

    def test_user_group_role_check_fails(self):
        user_id = uuid.uuid4().hex
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.check,
            role=ref['id'],
            project=project_id,
            group=group_id,
            user=user_id)

    def test_user_group_role_revoke_fails(self):
        user_id = uuid.uuid4().hex
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.revoke,
            role=ref['id'],
            project=project_id,
            group=group_id,
            user=user_id)


class DeprecatedImpliedRoleTests(utils.ClientTestCase):
    def setUp(self):
        super(DeprecatedImpliedRoleTests, self).setUp()
        self.key = 'role'
        self.collection_key = 'roles'
        self.model = roles.Role
        self.manager = self.client.roles

    def test_implied_create(self):
        prior_id = uuid.uuid4().hex
        prior_name = uuid.uuid4().hex
        implied_id = uuid.uuid4().hex
        implied_name = uuid.uuid4().hex

        mock_response = {
            "role_inference": {
                "implies": {
                    "id": implied_id,
                    "links": {"self": "http://host/v3/roles/%s" % implied_id},
                    "name": implied_name
                },
                "prior_role": {
                    "id": prior_id,
                    "links": {"self": "http://host/v3/roles/%s" % prior_id},
                    "name": prior_name
                }
            }
        }

        self.stub_url('PUT',
                      ['roles', prior_id, 'implies', implied_id],
                      json=mock_response,
                      status_code=201)

        with self.deprecations.expect_deprecations_here():
            manager_result = self.manager.create_implied(prior_id, implied_id)
            self.assertIsInstance(manager_result, roles.InferenceRule)
            self.assertEqual(mock_response['role_inference']['implies'],
                             manager_result.implies)
            self.assertEqual(mock_response['role_inference']['prior_role'],
                             manager_result.prior_role)


class ImpliedRoleTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(ImpliedRoleTests, self).setUp()
        self.key = 'role_inference'
        self.collection_key = 'role_inferences'
        self.model = roles.InferenceRule
        self.manager = self.client.inference_rules

    def test_check(self):
        prior_role_id = uuid.uuid4().hex
        implied_role_id = uuid.uuid4().hex
        self.stub_url('HEAD',
                      ['roles', prior_role_id, 'implies', implied_role_id],
                      status_code=204)

        result = self.manager.check(prior_role_id, implied_role_id)
        self.assertTrue(result)

    def test_get(self):
        prior_id = uuid.uuid4().hex
        prior_name = uuid.uuid4().hex
        implied_id = uuid.uuid4().hex
        implied_name = uuid.uuid4().hex

        mock_response = {
            "role_inference": {
                "implies": {
                    "id": implied_id,
                    "links": {"self": "http://host/v3/roles/%s" % implied_id},
                    "name": implied_name
                },
                "prior_role": {
                    "id": prior_id,
                    "links": {"self": "http://host/v3/roles/%s" % prior_id},
                    "name": prior_name
                }
            }
        }

        self.stub_url('GET',
                      ['roles', prior_id, 'implies', implied_id],
                      json=mock_response,
                      status_code=200)

        manager_result = self.manager.get(prior_id, implied_id)
        self.assertIsInstance(manager_result, roles.InferenceRule)
        self.assertEqual(mock_response['role_inference']['implies'],
                         manager_result.implies)
        self.assertEqual(mock_response['role_inference']['prior_role'],
                         manager_result.prior_role)

    def test_create(self):
        prior_id = uuid.uuid4().hex
        prior_name = uuid.uuid4().hex
        implied_id = uuid.uuid4().hex
        implied_name = uuid.uuid4().hex

        mock_response = {
            "role_inference": {
                "implies": {
                    "id": implied_id,
                    "links": {"self": "http://host/v3/roles/%s" % implied_id},
                    "name": implied_name
                },
                "prior_role": {
                    "id": prior_id,
                    "links": {"self": "http://host/v3/roles/%s" % prior_id},
                    "name": prior_name
                }
            }
        }

        self.stub_url('PUT',
                      ['roles', prior_id, 'implies', implied_id],
                      json=mock_response,
                      status_code=201)

        manager_result = self.manager.create(prior_id, implied_id)

        self.assertIsInstance(manager_result, roles.InferenceRule)
        self.assertEqual(mock_response['role_inference']['implies'],
                         manager_result.implies)
        self.assertEqual(mock_response['role_inference']['prior_role'],
                         manager_result.prior_role)

    def test_delete(self):
        prior_role_id = uuid.uuid4().hex
        implied_role_id = uuid.uuid4().hex
        self.stub_url('DELETE',
                      ['roles', prior_role_id, 'implies', implied_role_id],
                      status_code=204)

        status, body = self.manager.delete(prior_role_id, implied_role_id)
        self.assertEqual(204, status.status_code)
        self.assertIsNone(body)

    def test_list_role_inferences(self):
        prior_id = uuid.uuid4().hex
        prior_name = uuid.uuid4().hex
        implied_id = uuid.uuid4().hex
        implied_name = uuid.uuid4().hex

        mock_response = {
            "role_inferences": [{
                "implies": [{
                    "id": implied_id,
                    "links": {"self": "http://host/v3/roles/%s" % implied_id},
                    "name": implied_name
                }],
                "prior_role": {
                    "id": prior_id,
                    "links": {"self": "http://host/v3/roles/%s" % prior_id},
                    "name": prior_name
                }
            }]
        }

        self.stub_url('GET',
                      ['role_inferences'],
                      json=mock_response,
                      status_code=200)
        manager_result = self.manager.list_inference_roles()
        self.assertEqual(1, len(manager_result))
        self.assertIsInstance(manager_result[0], roles.InferenceRule)
        self.assertEqual(mock_response['role_inferences'][0]['implies'],
                         manager_result[0].implies)
        self.assertEqual(mock_response['role_inferences'][0]['prior_role'],
                         manager_result[0].prior_role)

    def test_list(self):
        prior_id = uuid.uuid4().hex
        prior_name = uuid.uuid4().hex
        implied_id = uuid.uuid4().hex
        implied_name = uuid.uuid4().hex

        mock_response = {
            "role_inference": {
                "implies": [{
                    "id": implied_id,
                    "links": {"self": "http://host/v3/roles/%s" % implied_id},
                    "name": implied_name
                }],
                "prior_role": {
                    "id": prior_id,
                    "links": {"self": "http://host/v3/roles/%s" % prior_id},
                    "name": prior_name
                }
            },
            "links": {"self": "http://host/v3/roles/%s/implies" % prior_id}
        }

        self.stub_url('GET',
                      ['roles', prior_id, 'implies'],
                      json=mock_response,
                      status_code=200)

        manager_result = self.manager.list(prior_id)
        self.assertIsInstance(manager_result, roles.InferenceRule)
        self.assertEqual(1, len(manager_result.implies))
        self.assertEqual(mock_response['role_inference']['implies'],
                         manager_result.implies)
        self.assertEqual(mock_response['role_inference']['prior_role'],
                         manager_result.prior_role)

    def test_update(self):
        # Update not supported for rule inferences
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.update)

    def test_find(self):
        # Find not supported for rule inferences
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.find)

    def test_put(self):
        # Put not supported for rule inferences
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.put)

    def test_list_params(self):
        # Put not supported for rule inferences
        self.skipTest("list params not supported by rule inferences")
