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
