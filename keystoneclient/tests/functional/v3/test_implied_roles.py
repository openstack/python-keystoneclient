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
from keystoneclient.tests.functional.v3 import client_fixtures as fixtures


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

inference_rules = {"test_admin": "test_policy_manager",
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

    def test_implied_roles(self):
        initial_rule_count = (
            len(self.client.inference_rules.list_inference_roles()))

        self.create_roles()
        self.create_rules()
        rule_count = len(self.client.inference_rules.list_inference_roles())
        self.assertEqual(initial_rule_count + len(inference_rules),
                         rule_count)

    def role_dict(self):
        roles = {role.name: role.id for role in self.client.roles.list()}
        return roles

    def create_roles(self):
        for role_def in role_defs:
            role = fixtures.Role(self.client, name=role_def)
            self.useFixture(role)

    def create_rules(self):
        roles = self.role_dict()
        for prior, implied in inference_rules.items():
            rule = fixtures.InferenceRule(self.client, roles[prior],
                                          roles[implied])
            self.useFixture(rule)
