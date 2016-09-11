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

    def test_implied_role_check(self):
        prior_role_id = uuid.uuid4().hex
        implied_role_id = uuid.uuid4().hex
        self.stub_url('HEAD',
                      ['roles', prior_role_id, 'implies', implied_role_id],
                      status_code=200)

        self.manager.check_implied(prior_role_id, implied_role_id)

    def test_implied_role_get(self):
        prior_role_id = uuid.uuid4().hex
        implied_role_id = uuid.uuid4().hex
        self.stub_url('GET',
                      ['roles', prior_role_id, 'implies', implied_role_id],
                      json={'role': {}},
                      status_code=204)

        self.manager.get_implied(prior_role_id, implied_role_id)

    def test_implied_role_create(self):
        prior_role_id = uuid.uuid4().hex
        implied_role_id = uuid.uuid4().hex
        test_json = {
            "role_inference": {
                "prior_role": {
                    "id": prior_role_id,
                    "links": {},
                    "name": "prior role name"
                },
                "implies": {
                    "id": implied_role_id,
                    "links": {},
                    "name": "implied role name"
                }
            },
            "links": {}
        }

        self.stub_url('PUT',
                      ['roles', prior_role_id, 'implies', implied_role_id],
                      json=test_json,
                      status_code=200)

        returned_rule = self.manager.create_implied(
            prior_role_id, implied_role_id)

        self.assertEqual(test_json['role_inference']['implies'],
                         returned_rule.implies)
        self.assertEqual(test_json['role_inference']['prior_role'],
                         returned_rule.prior_role)

    def test_implied_role_delete(self):
        prior_role_id = uuid.uuid4().hex
        implied_role_id = uuid.uuid4().hex
        self.stub_url('DELETE',
                      ['roles', prior_role_id, 'implies', implied_role_id],
                      status_code=200)

        self.manager.delete_implied(prior_role_id, implied_role_id)

    def test_list_role_inferences(self, **kwargs):
        self.stub_url('GET',
                      ['role_inferences', ''],
                      json={'role_inferences': {}},
                      status_code=204)

        self.manager.list_role_inferences()
