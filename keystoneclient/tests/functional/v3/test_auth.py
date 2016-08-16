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


class AuthTestCase(base.V3ClientTestCase):

    def test_projects(self):
        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        role = fixtures.Role(self.client)
        self.useFixture(role)
        self.client.roles.grant(role.id, user=self.user_id, project=project.id)

        projects = self.client.auth.projects()
        self.assertIn(project.entity, projects)

    def test_domains(self):
        domain = fixtures.Domain(self.client)
        self.useFixture(domain)

        role = fixtures.Role(self.client)
        self.useFixture(role)
        self.client.roles.grant(role.id, user=self.user_id, domain=domain.id)

        domains = self.client.auth.domains()
        self.assertIn(domain.entity, domains)
