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

from keystoneauth1.exceptions import http
from keystoneclient.tests.functional import base
from keystoneclient.tests.functional.v3 import client_fixtures as fixtures


class UsersTestCase(base.V3ClientTestCase):

    def check_user(self, user, user_ref=None):
        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user.enabled)
        self.assertIn('self', user.links)
        self.assertIn('/users/' + user.id, user.links['self'])

        if user_ref:
            self.assertEqual(user_ref['name'], user.name)
            self.assertEqual(user_ref['domain'], user.domain_id)
            # There is no guarantee the attributes below are present in user
            if hasattr(user_ref, 'description'):
                self.assertEqual(user_ref['description'], user.description)
            if hasattr(user_ref, 'email'):
                self.assertEqual(user_ref['email'], user.email)
            if hasattr(user_ref, 'default_project'):
                self.assertEqual(user_ref['default_project'],
                                 user.default_project_id)
        else:
            # Only check remaining mandatory attributes
            self.assertIsNotNone(user.name)
            self.assertIsNotNone(user.domain_id)

    def test_create_user(self):
        user_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'domain': self.project_domain_id,
            'default_project': self.project_id,
            'password': uuid.uuid4().hex,
            'description': uuid.uuid4().hex}

        user = self.client.users.create(**user_ref)
        self.addCleanup(self.client.users.delete, user)
        self.check_user(user, user_ref)

    def test_get_user(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)

        user_ret = self.client.users.get(user.id)
        self.check_user(user_ret, user.ref)

    def test_list_users(self):
        user_one = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user_one)

        user_two = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user_two)

        users = self.client.users.list()

        # All users are valid
        for user in users:
            self.check_user(user)

        self.assertIn(user_one.entity, users)
        self.assertIn(user_two.entity, users)

    def test_update_user(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)

        new_description = uuid.uuid4().hex
        user_ret = self.client.users.update(user.id,
                                            description=new_description)

        user.ref.update({'description': new_description})
        self.check_user(user_ret, user.ref)

    def test_user_grouping(self):
        # keystoneclient.v3.users owns user grouping operations, this is why
        # this test case belongs to this class
        user = fixtures.User(self.client, self.project_domain_id)
        group = fixtures.Group(self.client, self.project_domain_id)
        self.useFixture(user)
        self.useFixture(group)

        self.assertRaises(http.NotFound,
                          self.client.users.check_in_group,
                          user.id, group.id)

        self.client.users.add_to_group(user.id, group.id)
        self.client.users.check_in_group(user.id, group.id)
        self.client.users.remove_from_group(user.id, group.id)

        self.assertRaises(http.NotFound,
                          self.client.users.check_in_group,
                          user.id, group.id)

    def test_delete_user(self):
        user = self.client.users.create(name=uuid.uuid4().hex,
                                        domain=self.project_domain_id)

        self.client.users.delete(user.id)
        self.assertRaises(http.NotFound,
                          self.client.users.get,
                          user.id)
