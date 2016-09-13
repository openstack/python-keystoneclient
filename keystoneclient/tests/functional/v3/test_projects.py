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
from keystoneclient import exceptions
from keystoneclient.tests.functional import base
from keystoneclient.tests.functional.v3 import client_fixtures as fixtures


class ProjectsTestCase(base.V3ClientTestCase):

    def check_project(self, project, project_ref=None):
        self.assertIsNotNone(project.id)
        self.assertIn('self', project.links)
        self.assertIn('/projects/' + project.id, project.links['self'])

        if project_ref:
            self.assertEqual(project_ref['name'], project.name)
            self.assertEqual(project_ref['domain'], project.domain_id)
            self.assertEqual(project_ref['enabled'], project.enabled)

            # There is no guarantee the attributes below are present in project
            if hasattr(project_ref, 'description'):
                self.assertEqual(project_ref['description'],
                                 project.description)
            if hasattr(project_ref, 'parent'):
                self.assertEqual(project_ref['parent'], project.parent)

        else:
            # Only check remaining mandatory attributes
            self.assertIsNotNone(project.name)
            self.assertIsNotNone(project.domain_id)
            self.assertIsNotNone(project.enabled)

    def test_create_subproject(self):
        project_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'domain': self.project_domain_id,
            'enabled': True,
            'description': uuid.uuid4().hex,
            'parent': self.project_id}

        project = self.client.projects.create(**project_ref)
        self.addCleanup(self.client.projects.delete, project)
        self.check_project(project, project_ref)

    def test_create_project(self):
        project_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'domain': self.project_domain_id,
            'enabled': True,
            'description': uuid.uuid4().hex}

        project = self.client.projects.create(**project_ref)
        self.addCleanup(self.client.projects.delete, project)
        self.check_project(project, project_ref)

    def test_get_project(self):
        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        project_ret = self.client.projects.get(project.id)
        self.check_project(project_ret, project.ref)

    def test_get_project_invalid_params(self):
        self.assertRaises(exceptions.ValidationError,
                          self.client.projects.get,
                          self.project_id,
                          subtree_as_list=True, subtree_as_ids=True)
        self.assertRaises(exceptions.ValidationError,
                          self.client.projects.get,
                          self.project_id,
                          parents_as_list=True, parents_as_ids=True)

    def test_get_hierarchy_as_list(self):
        parent_project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(parent_project)

        project = fixtures.Project(self.client, self.project_domain_id,
                                   parent=parent_project.id)
        self.useFixture(project)

        child_project = fixtures.Project(self.client, self.project_domain_id,
                                         parent=project.id)
        self.useFixture(child_project)

        # Only parents and subprojects that the current user has role
        # assingments on are returned when asked for subtree_as_list and
        # parents_as_list.
        role = fixtures.Role(self.client)
        self.useFixture(role)
        self.client.roles.grant(role.id, user=self.user_id,
                                project=parent_project.id)
        self.client.roles.grant(role.id, user=self.user_id, project=project.id)
        self.client.roles.grant(role.id, user=self.user_id,
                                project=child_project.id)

        project_ret = self.client.projects.get(project.id,
                                               subtree_as_list=True,
                                               parents_as_list=True)

        self.check_project(project_ret, project.ref)
        self.assertItemsEqual([{'project': parent_project.entity.to_dict()}],
                              project_ret.parents)
        self.assertItemsEqual([{'project': child_project.entity.to_dict()}],
                              project_ret.subtree)

    def test_get_hierarchy_as_ids(self):
        parent_project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(parent_project)

        project = fixtures.Project(self.client, self.project_domain_id,
                                   parent=parent_project.id)
        self.useFixture(project)

        child_project = fixtures.Project(self.client, self.project_domain_id,
                                         parent=project.id)
        self.useFixture(child_project)

        project_ret = self.client.projects.get(project.id,
                                               subtree_as_ids=True,
                                               parents_as_ids=True)

        self.assertItemsEqual([parent_project.id], project_ret.parents)
        self.assertItemsEqual([child_project.id], project_ret.subtree)

    def test_list_projects(self):
        project_one = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project_one)

        project_two = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project_two)

        projects = self.client.projects.list()

        # All projects are valid
        for project in projects:
            self.check_project(project)

        self.assertIn(project_one.entity, projects)
        self.assertIn(project_two.entity, projects)

    def test_update_project(self):
        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        new_name = fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex
        new_description = uuid.uuid4().hex
        project_ret = self.client.projects.update(project.id,
                                                  name=new_name,
                                                  enabled=False,
                                                  description=new_description)

        project.ref.update({'name': new_name, 'enabled': False,
                            'description': new_description})
        self.check_project(project_ret, project.ref)

    def test_update_project_domain_not_allowed(self):
        project = fixtures.Project(self.client)
        self.useFixture(project)

        domain = fixtures.Domain(self.client)
        self.useFixture(domain)
        # Cannot update domain after project is created.
        self.assertRaises(http.BadRequest,
                          self.client.projects.update,
                          project.id, domain=domain.id)

    def test_delete_project(self):
        project = self.client.projects.create(name=uuid.uuid4().hex,
                                              domain=self.project_domain_id,
                                              enabled=True)

        self.client.projects.delete(project.id)
        self.assertRaises(http.NotFound,
                          self.client.projects.get,
                          project.id)
