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


class EC2TestCase(base.V3ClientTestCase):

    def check_ec2(self, ec2, ec2_ref=None):
        self.assertIn('self', ec2.links)
        self.assertIn('/users/%s/credentials/OS-EC2/%s'
                      % (ec2.user_id, ec2.access), ec2.links['self'])

        if ec2_ref:
            self.assertEqual(ec2_ref['user_id'], ec2.user_id)
            self.assertEqual(ec2_ref['project_id'], ec2.tenant_id)

        else:
            self.assertIsNotNone(ec2.user_id)
            self.assertIsNotNone(ec2.tenant_id)

    def test_create_ec2(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)
        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        ec2_ref = {'user_id': user.id,
                   'project_id': project.id}
        ec2 = self.client.ec2.create(**ec2_ref)

        self.addCleanup(self.client.ec2.delete, user.id, ec2.access)
        self.check_ec2(ec2, ec2_ref)

    def test_get_ec2(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)
        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        ec2 = fixtures.EC2(self.client, user_id=user.id, project_id=project.id)
        self.useFixture(ec2)

        ec2_ret = self.client.ec2.get(user.id, ec2.access)
        self.check_ec2(ec2_ret, ec2.ref)

    def test_list_ec2(self):
        user_one = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user_one)
        ec2_one = fixtures.EC2(self.client, user_id=user_one.id,
                               project_id=self.project_domain_id)
        self.useFixture(ec2_one)

        user_two = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user_two)
        ec2_two = fixtures.EC2(self.client, user_id=user_two.id,
                               project_id=self.project_domain_id)
        self.useFixture(ec2_two)

        ec2_list = self.client.ec2.list(user_one.id)

        # All ec2 are valid
        for ec2 in ec2_list:
            self.check_ec2(ec2)

        self.assertIn(ec2_one.entity, ec2_list)
        self.assertNotIn(ec2_two.entity, ec2_list)

    def test_delete_ec2(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)
        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        ec2 = self.client.ec2.create(user.id, project.id)

        self.client.ec2.delete(user.id, ec2.access)
        self.assertRaises(http.NotFound,
                          self.client.ec2.get,
                          user.id, ec2.access)
