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


class PoliciesTestCase(base.V3ClientTestCase):

    def check_policy(self, policy, policy_ref=None):
        self.assertIsNotNone(policy.id)
        self.assertIn('self', policy.links)
        self.assertIn('/policies/' + policy.id, policy.links['self'])

        if policy_ref:
            self.assertEqual(policy_ref['blob'], policy.blob)
            self.assertEqual(policy_ref['type'], policy.type)

        else:
            # Only check remaining mandatory attributes
            self.assertIsNotNone(policy.blob)
            self.assertIsNotNone(policy.type)

    def test_create_policy(self):
        policy_ref = {'blob': uuid.uuid4().hex,
                      'type': uuid.uuid4().hex}

        policy = self.client.policies.create(**policy_ref)
        self.addCleanup(self.client.policies.delete, policy)
        self.check_policy(policy, policy_ref)

    def test_get_policy(self):
        policy = fixtures.Policy(self.client)
        self.useFixture(policy)

        policy_ret = self.client.policies.get(policy.id)
        self.check_policy(policy_ret, policy.ref)

    def test_list_policies(self):
        policy_one = fixtures.Policy(self.client)
        self.useFixture(policy_one)

        policy_two = fixtures.Policy(self.client)
        self.useFixture(policy_two)

        policies = self.client.policies.list()

        # All policies are valid
        for policy in policies:
            self.check_policy(policy)

        self.assertIn(policy_one.entity, policies)
        self.assertIn(policy_two.entity, policies)

    def test_update_policy(self):
        policy = fixtures.Policy(self.client)
        self.useFixture(policy)

        new_blob = uuid.uuid4().hex
        new_type = uuid.uuid4().hex

        policy_ret = self.client.policies.update(policy.id,
                                                 blob=new_blob,
                                                 type=new_type)

        policy.ref.update({'blob': new_blob, 'type': new_type})
        self.check_policy(policy_ret, policy.ref)

    def test_delete_policy(self):
        policy = self.client.policies.create(blob=uuid.uuid4().hex,
                                             type=uuid.uuid4().hex)

        self.client.policies.delete(policy.id)
        self.assertRaises(http.NotFound,
                          self.client.policies.get,
                          policy.id)
