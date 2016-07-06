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

import fixtures
import uuid


RESOURCE_NAME_PREFIX = 'keystoneclient-functional-'


class Base(fixtures.Fixture):

    def __init__(self, client, domain_id=None):
        super(Base, self).__init__()

        self.client = client
        self.domain_id = domain_id
        self.ref = None
        self.entity = None

    def __getattr__(self, name):
        """Return the attribute from the represented entity."""
        return getattr(self.entity, name)


class User(Base):

    def setUp(self):
        super(User, self).setUp()

        self.ref = {'name': RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
                    'domain': self.domain_id}
        self.entity = self.client.users.create(**self.ref)
        self.addCleanup(self.client.users.delete, self.entity)


class Group(Base):

    def setUp(self):
        super(Group, self).setUp()

        self.ref = {'name': RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
                    'domain': self.domain_id}
        self.entity = self.client.groups.create(**self.ref)
        self.addCleanup(self.client.groups.delete, self.entity)


class Domain(Base):

    def setUp(self):
        super(Domain, self).setUp()

        self.ref = {'name': RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
                    'description': uuid.uuid4().hex,
                    'enabled': True}
        self.entity = self.client.domains.create(**self.ref)

        # Only disabled domains can be deleted
        self.addCleanup(self.client.domains.delete, self.entity)
        self.addCleanup(self.client.domains.update, self.entity, enabled=False)


class Project(Base):

    def __init__(self, client, domain_id=None, parent=None):
        super(Project, self).__init__(client, domain_id)
        self.parent = parent

    def setUp(self):
        super(Project, self).setUp()

        self.ref = {'name': RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
                    'domain': self.domain_id,
                    'enabled': True,
                    'parent': self.parent}
        self.entity = self.client.projects.create(**self.ref)
        self.addCleanup(self.client.projects.delete, self.entity)


class Role(Base):

    def setUp(self):
        super(Role, self).setUp()

        self.ref = {'name': RESOURCE_NAME_PREFIX + uuid.uuid4().hex}
        self.entity = self.client.roles.create(**self.ref)
        self.addCleanup(self.client.roles.delete, self.entity)


class Service(Base):

    def setUp(self):
        super(Service, self).setUp()

        self.ref = {'name': RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
                    'type': uuid.uuid4().hex,
                    'enabled': True,
                    'description': uuid.uuid4().hex}
        self.entity = self.client.services.create(**self.ref)
        self.addCleanup(self.client.services.delete, self.entity)


class Policy(Base):

    def setUp(self):
        super(Policy, self).setUp()

        self.ref = {'blob': uuid.uuid4().hex,
                    'type': uuid.uuid4().hex}
        self.entity = self.client.policies.create(**self.ref)
        self.addCleanup(self.client.policies.delete, self.entity)
