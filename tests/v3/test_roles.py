# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC
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

import httpretty

from keystoneclient import exceptions
from keystoneclient.v3 import roles
from tests.v3 import utils


class RoleTests(utils.TestCase, utils.CrudTests):
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

    @httpretty.activate
    def test_domain_role_grant(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.PUT,
                      ['domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status=201)

        self.manager.grant(role=ref['id'], domain=domain_id, user=user_id)

    @httpretty.activate
    def test_domain_group_role_grant(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.PUT,
                      ['domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status=201)

        self.manager.grant(role=ref['id'], domain=domain_id, group=group_id)

    @httpretty.activate
    def test_domain_role_list(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity(httpretty.GET,
                         ['domains', domain_id, 'users', user_id,
                         self.collection_key], entity=ref_list)

        self.manager.list(domain=domain_id, user=user_id)

    @httpretty.activate
    def test_domain_group_role_list(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity(httpretty.GET,
                         ['domains', domain_id, 'groups', group_id,
                          self.collection_key], entity=ref_list)

        self.manager.list(domain=domain_id, group=group_id)

    @httpretty.activate
    def test_domain_role_check(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.HEAD,
                      ['domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status=204)

        self.manager.check(role=ref['id'], domain=domain_id,
                           user=user_id)

    @httpretty.activate
    def test_domain_group_role_check(self):
        return
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.HEAD,
                      ['domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status=204)

        self.manager.check(role=ref['id'], domain=domain_id, group=group_id)

    @httpretty.activate
    def test_domain_role_revoke(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.DELETE,
                      ['domains', domain_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status=204)

        self.manager.revoke(role=ref['id'], domain=domain_id, user=user_id)

    @httpretty.activate
    def test_domain_group_role_revoke(self):
        group_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.DELETE,
                      ['domains', domain_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status=204)

        self.manager.revoke(role=ref['id'], domain=domain_id, group=group_id)

    @httpretty.activate
    def test_project_role_grant(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.PUT,
                      ['projects', project_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status=201)

        self.manager.grant(role=ref['id'], project=project_id, user=user_id)

    @httpretty.activate
    def test_project_group_role_grant(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.PUT,
                      ['projects', project_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status=201)

        self.manager.grant(role=ref['id'], project=project_id, group=group_id)

    @httpretty.activate
    def test_project_role_list(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity(httpretty.GET,
                         ['projects', project_id, 'users', user_id,
                          self.collection_key], entity=ref_list)

        self.manager.list(project=project_id, user=user_id)

    @httpretty.activate
    def test_project_group_role_list(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]

        self.stub_entity(httpretty.GET,
                         ['projects', project_id, 'groups', group_id,
                          self.collection_key], entity=ref_list)

        self.manager.list(project=project_id, group=group_id)

    @httpretty.activate
    def test_project_role_check(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.HEAD,
                      ['projects', project_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status=200)

        self.manager.check(role=ref['id'], project=project_id, user=user_id)

    @httpretty.activate
    def test_project_group_role_check(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.HEAD,
                      ['projects', project_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status=200)

        self.manager.check(role=ref['id'], project=project_id, group=group_id)

    @httpretty.activate
    def test_project_role_revoke(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.DELETE,
                      ['projects', project_id, 'users', user_id,
                       self.collection_key, ref['id']],
                      status=204)

        self.manager.revoke(role=ref['id'], project=project_id, user=user_id)

    @httpretty.activate
    def test_project_group_role_revoke(self):
        group_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.stub_url(httpretty.DELETE,
                      ['projects', project_id, 'groups', group_id,
                       self.collection_key, ref['id']],
                      status=204)

        self.manager.revoke(role=ref['id'], project=project_id, group=group_id)

    @httpretty.activate
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
