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

from keystoneclient.tests.functional import base

role_defs = ["test_admin",
             "test_id_manager",
             "test_resource_manager",
             "test_role_manager",
             "test_assignment_manager",
             "test_domain_manager",
             "test_project_manager",
             "test_catalog_manager",
             "test_policy_manager",
             "test_observer",
             "test_domain_tech_lead",
             "test_project_observer",
             "test_member"]

inference_rules = {"test_admin": "test_id_manager",
                   "test_admin": "test_resource_manager",
                   "test_admin": "test_role_manager",
                   "test_admin": "test_catalog_manager",
                   "test_admin": "test_policy_manager",
                   "test_id_manager": "test_project_observer",
                   "test_resource_manager": "test_project_observer",
                   "test_role_manager": "test_project_observer",
                   "test_catalog_manager": "test_project_observer",
                   "test_policy_manager": "test_project_observer",
                   "test_project_observer": "test_observer",
                   "test_member": "test_observer"}


class TestImpliedRoles(base.V3ClientTestCase):

    def setUp(self):
        super(TestImpliedRoles, self).setUp()
        self.delete_rules()
        self.delete_roles()

    def test_implied_roles(self):

        initial_role_count = len(self.client.roles.list())
        initial_rule_count = len(self.client.roles.list_role_inferences())

        self.create_roles()
        self.create_rules()
        role_count = len(self.client.roles.list())
        self.assertEqual(initial_role_count + len(role_defs),
                         role_count)
        rule_count = len(self.client.roles.list_role_inferences())
        self.assertEqual(initial_rule_count + len(inference_rules),
                         rule_count)

        self.delete_rules()
        self.delete_roles()
        role_count = len(self.client.roles.list())
        self.assertEqual(initial_role_count, role_count)
        rule_count = len(self.client.roles.list_role_inferences())
        self.assertEqual(initial_rule_count, rule_count)

    def role_dict(self):
        roles = {role.name: role.id for role in self.client.roles.list()}
        return roles

    def create_roles(self):
        for role_def in role_defs:
            self.client.roles.create(role_def)

    def delete_roles(self):
        roles = self.role_dict()
        for role_def in role_defs:
            print ("role %s" % role_def)
            try:
                self.client.roles.delete(roles[role_def])
            except KeyError:
                pass

    def create_rules(self):
        roles = self.role_dict()
        for prior, implied in inference_rules.items():
            self.client.roles.create_implied(roles[prior], roles[implied])

    def delete_rules(self):
        roles = self.role_dict()
        for prior, implied in inference_rules.items():
            try:
                self.client.roles.delete_implied(roles[prior], roles[implied])
            except KeyError:
                pass
