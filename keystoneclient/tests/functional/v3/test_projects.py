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


class ProjectsTestMixin(object):

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


class ProjectsTestCase(base.V3ClientTestCase, ProjectsTestMixin):

    def setUp(self):
        super(ProjectsTestCase, self).setUp()
        self.test_domain = fixtures.Domain(self.client)
        self.useFixture(self.test_domain)

        self.test_project = fixtures.Project(self.client, self.test_domain.id)
        self.useFixture(self.test_project)
        self.special_tag = '~`!@#$%^&*()-_+=<>.? \'"'

    def test_create_subproject(self):
        project_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'domain': self.test_domain.id,
            'enabled': True,
            'description': uuid.uuid4().hex,
            'parent': self.test_project.id}

        project = self.client.projects.create(**project_ref)
        self.addCleanup(self.client.projects.delete, project)
        self.check_project(project, project_ref)

    def test_create_project(self):
        project_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'domain': self.test_domain.id,
            'enabled': True,
            'description': uuid.uuid4().hex}

        project = self.client.projects.create(**project_ref)
        self.addCleanup(self.client.projects.delete, project)
        self.check_project(project, project_ref)

    def test_get_project(self):
        project_ret = self.client.projects.get(self.test_project.id)
        self.check_project(project_ret, self.test_project.ref)

    def test_get_project_invalid_params(self):
        self.assertRaises(exceptions.ValidationError,
                          self.client.projects.get,
                          self.test_project.id,
                          subtree_as_list=True, subtree_as_ids=True)
        self.assertRaises(exceptions.ValidationError,
                          self.client.projects.get,
                          self.test_project.id,
                          parents_as_list=True, parents_as_ids=True)

    def test_get_hierarchy_as_list(self):
        project = fixtures.Project(self.client, self.test_domain.id,
                                   parent=self.test_project.id)
        self.useFixture(project)

        child_project = fixtures.Project(self.client, self.test_domain.id,
                                         parent=project.id)
        self.useFixture(child_project)

        # Only parents and subprojects that the current user has role
        # assingments on are returned when asked for subtree_as_list and
        # parents_as_list.
        role = fixtures.Role(self.client)
        self.useFixture(role)
        self.client.roles.grant(role.id, user=self.user_id,
                                project=self.test_project.id)
        self.client.roles.grant(role.id, user=self.user_id,
                                project=project.id)
        self.client.roles.grant(role.id, user=self.user_id,
                                project=child_project.id)

        project_ret = self.client.projects.get(project.id,
                                               subtree_as_list=True,
                                               parents_as_list=True)

        self.check_project(project_ret, project.ref)
        self.assertItemsEqual(
            [{'project': self.test_project.entity.to_dict()}],
            project_ret.parents)
        self.assertItemsEqual(
            [{'project': child_project.entity.to_dict()}],
            project_ret.subtree)

    def test_get_hierarchy_as_ids(self):
        project = fixtures.Project(self.client, self.test_domain.id,
                                   parent=self.test_project.id)
        self.useFixture(project)

        child_project = fixtures.Project(self.client, self.test_domain.id,
                                         parent=project.id)
        self.useFixture(child_project)

        project_ret = self.client.projects.get(project.id,
                                               subtree_as_ids=True,
                                               parents_as_ids=True)

        self.assertItemsEqual([self.test_project.id], project_ret.parents)
        self.assertItemsEqual([child_project.id], project_ret.subtree)

    def test_list_projects(self):
        project_one = fixtures.Project(self.client, self.test_domain.id)
        self.useFixture(project_one)

        project_two = fixtures.Project(self.client, self.test_domain.id)
        self.useFixture(project_two)

        projects = self.client.projects.list()

        # All projects are valid
        for project in projects:
            self.check_project(project)

        self.assertIn(project_one.entity, projects)
        self.assertIn(project_two.entity, projects)

    def test_update_project(self):
        project = fixtures.Project(self.client, self.test_domain.id)
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
        domain = fixtures.Domain(self.client)
        self.useFixture(domain)
        # Cannot update domain after project is created.
        self.assertRaises(http.BadRequest,
                          self.client.projects.update,
                          self.test_project.id, domain=domain.id)

    def test_delete_project(self):
        project = self.client.projects.create(name=uuid.uuid4().hex,
                                              domain=self.test_domain.id,
                                              enabled=True)

        self.client.projects.delete(project.id)
        self.assertRaises(http.NotFound,
                          self.client.projects.get,
                          project.id)

    def test_list_projects_with_tag_filters(self):
        project_one = fixtures.Project(
            self.client, self.test_domain.id,
            tags=['tag1'])
        project_two = fixtures.Project(
            self.client, self.test_domain.id,
            tags=['tag1', 'tag2'])
        project_three = fixtures.Project(
            self.client, self.test_domain.id,
            tags=['tag2', 'tag3'])

        self.useFixture(project_one)
        self.useFixture(project_two)
        self.useFixture(project_three)

        projects = self.client.projects.list(tags='tag1')
        project_ids = []
        for project in projects:
            project_ids.append(project.id)
        self.assertIn(project_one.id, project_ids)

        projects = self.client.projects.list(tags_any='tag1')
        project_ids = []
        for project in projects:
            project_ids.append(project.id)
        self.assertIn(project_one.id, project_ids)
        self.assertIn(project_two.id, project_ids)

        projects = self.client.projects.list(not_tags='tag1')
        project_ids = []
        for project in projects:
            project_ids.append(project.id)
        self.assertNotIn(project_one.id, project_ids)

        projects = self.client.projects.list(not_tags_any='tag1,tag2')
        project_ids = []
        for project in projects:
            project_ids.append(project.id)
        self.assertNotIn(project_one.id, project_ids)
        self.assertNotIn(project_two.id, project_ids)
        self.assertNotIn(project_three.id, project_ids)

        projects = self.client.projects.list(tags='tag1,tag2')
        project_ids = []
        for project in projects:
            project_ids.append(project.id)
        self.assertNotIn(project_one.id, project_ids)
        self.assertIn(project_two.id, project_ids)
        self.assertNotIn(project_three.id, project_ids)

    def test_add_tag(self):
        project = fixtures.Project(self.client, self.test_domain.id)
        self.useFixture(project)

        tags = self.client.projects.get(project.id).tags
        self.assertEqual([], tags)

        project.add_tag('tag1')
        tags = self.client.projects.get(project.id).tags
        self.assertEqual(['tag1'], tags)

        # verify there is an error when you try to add the same tag
        self.assertRaises(http.BadRequest,
                          project.add_tag,
                          'tag1')

    def test_update_tags(self):
        project = fixtures.Project(self.client, self.test_domain.id)
        self.useFixture(project)

        tags = self.client.projects.get(project.id).tags
        self.assertEqual([], tags)

        project.update_tags(['tag1', 'tag2', self.special_tag])
        tags = self.client.projects.get(project.id).tags
        self.assertIn('tag1', tags)
        self.assertIn('tag2', tags)
        self.assertIn(self.special_tag, tags)
        self.assertEqual(3, len(tags))

        project.update_tags([])
        tags = self.client.projects.get(project.id).tags
        self.assertEqual([], tags)

        # cannot have duplicate tags in update
        self.assertRaises(http.BadRequest,
                          project.update_tags,
                          ['tag1', 'tag1'])

    def test_delete_tag(self):
        project = fixtures.Project(
            self.client, self.test_domain.id,
            tags=['tag1', self.special_tag])
        self.useFixture(project)

        project.delete_tag('tag1')
        tags = self.client.projects.get(project.id).tags
        self.assertEqual([self.special_tag], tags)

        project.delete_tag(self.special_tag)
        tags = self.client.projects.get(project.id).tags
        self.assertEqual([], tags)

    def test_delete_all_tags(self):
        project_one = fixtures.Project(
            self.client, self.test_domain.id,
            tags=['tag1'])

        project_two = fixtures.Project(
            self.client, self.test_domain.id,
            tags=['tag1', 'tag2', self.special_tag])

        project_three = fixtures.Project(
            self.client, self.test_domain.id,
            tags=[])

        self.useFixture(project_one)
        self.useFixture(project_two)
        self.useFixture(project_three)

        result_one = project_one.delete_all_tags()
        tags_one = self.client.projects.get(project_one.id).tags
        tags_two = self.client.projects.get(project_two.id).tags
        self.assertEqual([], result_one)
        self.assertEqual([], tags_one)
        self.assertIn('tag1', tags_two)

        result_two = project_two.delete_all_tags()
        tags_two = self.client.projects.get(project_two.id).tags
        self.assertEqual([], result_two)
        self.assertEqual([], tags_two)

        result_three = project_three.delete_all_tags()
        tags_three = self.client.projects.get(project_three.id).tags
        self.assertEqual([], result_three)
        self.assertEqual([], tags_three)

    def test_list_tags(self):
        tags_one = ['tag1']
        project_one = fixtures.Project(
            self.client, self.test_domain.id,
            tags=tags_one)

        tags_two = ['tag1', 'tag2']
        project_two = fixtures.Project(
            self.client, self.test_domain.id,
            tags=tags_two)

        tags_three = []
        project_three = fixtures.Project(
            self.client, self.test_domain.id,
            tags=tags_three)

        self.useFixture(project_one)
        self.useFixture(project_two)
        self.useFixture(project_three)

        result_one = project_one.list_tags()
        result_two = project_two.list_tags()
        result_three = project_three.list_tags()

        for tag in tags_one:
            self.assertIn(tag, result_one)
        self.assertEqual(1, len(result_one))

        for tag in tags_two:
            self.assertIn(tag, result_two)
        self.assertEqual(2, len(result_two))

        for tag in tags_three:
            self.assertIn(tag, result_three)
        self.assertEqual(0, len(result_three))

    def test_check_tag(self):
        project = fixtures.Project(
            self.client, self.test_domain.id,
            tags=['tag1'])
        self.useFixture(project)

        tags = self.client.projects.get(project.id).tags
        self.assertEqual(['tag1'], tags)
        self.assertTrue(project.check_tag('tag1'))
        self.assertFalse(project.check_tag('tag2'))
        self.assertFalse(project.check_tag(self.special_tag))

    def test_add_invalid_tags(self):
        project_one = fixtures.Project(
            self.client, self.test_domain.id)

        self.useFixture(project_one)

        self.assertRaises(exceptions.BadRequest,
                          project_one.add_tag,
                          ',')
        self.assertRaises(exceptions.BadRequest,
                          project_one.add_tag,
                          '/')
        self.assertRaises(exceptions.BadRequest,
                          project_one.add_tag,
                          '')

    def test_update_invalid_tags(self):
        tags_comma = ['tag1', ',']
        tags_slash = ['tag1', '/']
        tags_blank = ['tag1', '']
        project_one = fixtures.Project(
            self.client, self.test_domain.id)

        self.useFixture(project_one)

        self.assertRaises(exceptions.BadRequest,
                          project_one.update_tags,
                          tags_comma)
        self.assertRaises(exceptions.BadRequest,
                          project_one.update_tags,
                          tags_slash)
        self.assertRaises(exceptions.BadRequest,
                          project_one.update_tags,
                          tags_blank)

    def test_create_project_invalid_tags(self):
        project_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'domain': self.test_domain.id,
            'enabled': True,
            'description': uuid.uuid4().hex,
            'tags': ','}

        self.assertRaises(exceptions.BadRequest,
                          self.client.projects.create,
                          **project_ref)

        project_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'domain': self.test_domain.id,
            'enabled': True,
            'description': uuid.uuid4().hex,
            'tags': '/'}

        self.assertRaises(exceptions.BadRequest,
                          self.client.projects.create,
                          **project_ref)

        project_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'domain': self.test_domain.id,
            'enabled': True,
            'description': uuid.uuid4().hex,
            'tags': ''}

        self.assertRaises(exceptions.BadRequest,
                          self.client.projects.create,
                          **project_ref)
