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

from keystoneauth1.exceptions import http

from keystoneclient.tests.functional import base
from keystoneclient.tests.functional.v3 import client_fixtures as fixtures
from keystoneclient.tests.functional.v3 import test_endpoint_groups
from keystoneclient.tests.functional.v3 import test_projects


class EndpointFiltersTestCase(base.V3ClientTestCase,
                              test_endpoint_groups.EndpointGroupsTestMixin,
                              test_projects.ProjectsTestMixin):

    def setUp(self):
        super(EndpointFiltersTestCase, self).setUp()

        self.project = fixtures.Project(self.client)
        self.endpoint_group = fixtures.EndpointGroup(self.client)
        self.useFixture(self.project)
        self.useFixture(self.endpoint_group)

        self.client.endpoint_filter.add_endpoint_group_to_project(
            self.endpoint_group, self.project)

    def test_add_endpoint_group_to_project(self):
        project = fixtures.Project(self.client)
        endpoint_group = fixtures.EndpointGroup(self.client)
        self.useFixture(project)
        self.useFixture(endpoint_group)

        self.client.endpoint_filter.add_endpoint_group_to_project(
            endpoint_group, project)
        self.client.endpoint_filter.check_endpoint_group_in_project(
            endpoint_group, project)

    def test_delete_endpoint_group_from_project(self):
        self.client.endpoint_filter.delete_endpoint_group_from_project(
            self.endpoint_group, self.project)
        self.assertRaises(
            http.NotFound,
            self.client.endpoint_filter.check_endpoint_group_in_project,
            self.endpoint_group, self.project)

    def test_list_endpoint_groups_for_project(self):
        endpoint_group_two = fixtures.EndpointGroup(self.client)
        self.useFixture(endpoint_group_two)
        self.client.endpoint_filter.add_endpoint_group_to_project(
            endpoint_group_two, self.project)

        endpoint_groups = (
            self.client.endpoint_filter.list_endpoint_groups_for_project(
                self.project
            )
        )

        for endpoint_group in endpoint_groups:
            self.check_endpoint_group(endpoint_group)

        self.assertIn(self.endpoint_group.entity, endpoint_groups)
        self.assertIn(endpoint_group_two.entity, endpoint_groups)

    def test_list_projects_for_endpoint_group(self):
        project_two = fixtures.Project(self.client)
        self.useFixture(project_two)
        self.client.endpoint_filter.add_endpoint_group_to_project(
            self.endpoint_group, project_two)

        f = self.client.endpoint_filter.list_projects_for_endpoint_group
        projects = f(self.endpoint_group)

        for project in projects:
            self.check_project(project)

        self.assertIn(self.project.entity, projects)
        self.assertIn(project_two.entity, projects)
