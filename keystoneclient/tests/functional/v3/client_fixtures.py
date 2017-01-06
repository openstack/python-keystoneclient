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

    def __init__(self, client, name=None, domain=None):
        super(Role, self).__init__(client)
        self.name = name or RESOURCE_NAME_PREFIX + uuid.uuid4().hex
        self.domain = domain

    def setUp(self):
        super(Role, self).setUp()

        self.ref = {'name': self.name,
                    'domain': self.domain}
        self.entity = self.client.roles.create(**self.ref)
        self.addCleanup(self.client.roles.delete, self.entity)


class InferenceRule(Base):

    def __init__(self, client, prior_role, implied_role):
        super(InferenceRule, self).__init__(client)
        self.prior_role = prior_role
        self.implied_role = implied_role

    def setUp(self):
        super(InferenceRule, self).setUp()

        self.ref = {'prior_role': self.prior_role,
                    'implied_role': self.implied_role}
        self.entity = self.client.inference_rules.create(**self.ref)
        self.addCleanup(self.client.inference_rules.delete, self.prior_role,
                        self.implied_role)


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


class Region(Base):

    def __init__(self, client, parent_region=None):
        super(Region, self).__init__(client)
        self.parent_region = parent_region

    def setUp(self):
        super(Region, self).setUp()

        self.ref = {'description': uuid.uuid4().hex,
                    'parent_region': self.parent_region}
        self.entity = self.client.regions.create(**self.ref)
        self.addCleanup(self.client.regions.delete, self.entity)


class Endpoint(Base):

    def __init__(self, client, service, interface, region=None):
        super(Endpoint, self).__init__(client)
        self.service = service
        self.interface = interface
        self.region = region

    def setUp(self):
        super(Endpoint, self).setUp()

        self.ref = {'service': self.service,
                    'url': 'http://' + uuid.uuid4().hex,
                    'enabled': True,
                    'interface': self.interface,
                    'region': self.region}
        self.entity = self.client.endpoints.create(**self.ref)
        self.addCleanup(self.client.endpoints.delete, self.entity)


class EndpointGroup(Base):

    def setUp(self):
        super(EndpointGroup, self).setUp()

        self.ref = {'name': RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
                    'filters': {'interface': 'public'},
                    'description': uuid.uuid4().hex}
        self.entity = self.client.endpoint_groups.create(**self.ref)
        self.addCleanup(self.client.endpoint_groups.delete, self.entity)


class Credential(Base):

    def __init__(self, client, user, type, project=None):
        super(Credential, self).__init__(client)
        self.user = user
        self.type = type
        self.project = project

        if type == 'ec2':
            self.blob = ("{\"access\":\"" + uuid.uuid4().hex +
                         "\",\"secret\":\"secretKey\"}")
        else:
            self.blob = uuid.uuid4().hex

    def setUp(self):
        super(Credential, self).setUp()

        self.ref = {'user': self.user,
                    'type': self.type,
                    'blob': self.blob,
                    'project': self.project}
        self.entity = self.client.credentials.create(**self.ref)
        self.addCleanup(self.client.credentials.delete, self.entity)


class EC2(Base):

    def __init__(self, client, user_id, project_id):
        super(EC2, self).__init__(client)
        self.user_id = user_id
        self.project_id = project_id

    def setUp(self):
        super(EC2, self).setUp()

        self.ref = {'user_id': self.user_id,
                    'project_id': self.project_id}
        self.entity = self.client.ec2.create(**self.ref)
        self.addCleanup(self.client.ec2.delete,
                        self.user_id,
                        self.entity.access)


class DomainConfig(Base):

    def __init__(self, client, domain_id):
        super(DomainConfig, self).__init__(client, domain_id=domain_id)
        self.domain_id = domain_id

    def setUp(self):
        super(DomainConfig, self).setUp()

        self.ref = {'identity': {'driver': uuid.uuid4().hex},
                    'ldap': {'url': uuid.uuid4().hex}}
        self.entity = self.client.domain_configs.create(
            self.domain_id, self.ref)
        self.addCleanup(self.client.domain_configs.delete,
                        self.domain_id)
