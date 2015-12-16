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

from keystoneclient import fixture
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import auth


class AuthProjectsTest(utils.ClientTestCase):

    def setUp(self):
        super(AuthProjectsTest, self).setUp()

        self.v3token = fixture.V3Token()
        self.stub_auth(json=self.v3token)

        self.stub_url('GET',
                      [],
                      json={'version': fixture.V3Discovery(self.TEST_URL)})

    def create_resource(self, id=None, name=None, **kwargs):
        kwargs['id'] = id or uuid.uuid4().hex
        kwargs['name'] = name or uuid.uuid4().hex
        return kwargs

    def test_get_projects(self):
        body = {'projects': [self.create_resource(),
                             self.create_resource(),
                             self.create_resource()]}

        self.stub_url('GET', ['auth', 'projects'], json=body)

        projects = self.client.auth.projects()

        self.assertEqual(3, len(projects))

        for p in projects:
            self.assertIsInstance(p, auth.Project)

    def test_get_domains(self):
        body = {'domains': [self.create_resource(),
                            self.create_resource(),
                            self.create_resource()]}

        self.stub_url('GET', ['auth', 'domains'], json=body)

        domains = self.client.auth.domains()

        self.assertEqual(3, len(domains))

        for d in domains:
            self.assertIsInstance(d, auth.Domain)
