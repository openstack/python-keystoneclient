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
from keystoneclient.tests.functional import base
from keystoneclient.tests.functional.v3 import client_fixtures as fixtures


class DomainsTestCase(base.V3ClientTestCase):

    def check_domain(self, domain, domain_ref=None):
        self.assertIsNotNone(domain.id)
        self.assertIn('self', domain.links)
        self.assertIn('/domains/' + domain.id, domain.links['self'])

        if domain_ref:
            self.assertEqual(domain_ref['name'], domain.name)
            self.assertEqual(domain_ref['enabled'], domain.enabled)

            # There is no guarantee description is present in domain
            if hasattr(domain_ref, 'description'):
                self.assertEqual(domain_ref['description'], domain.description)
        else:
            # Only check remaining mandatory attributes
            self.assertIsNotNone(domain.name)
            self.assertIsNotNone(domain.enabled)

    def test_create_domain(self):
        domain_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'description': uuid.uuid4().hex,
            'enabled': True}
        domain = self.client.domains.create(**domain_ref)
        self.check_domain(domain, domain_ref)

        # Only disabled domains can be deleted
        self.addCleanup(self.client.domains.delete, domain)
        self.addCleanup(self.client.domains.update, domain, enabled=False)

    def test_get_domain(self):
        domain_id = self.project_domain_id
        domain_ret = self.client.domains.get(domain_id)
        self.check_domain(domain_ret)

    def test_list_domains(self):
        domain_one = fixtures.Domain(self.client)
        self.useFixture(domain_one)

        domain_two = fixtures.Domain(self.client)
        self.useFixture(domain_two)

        domains = self.client.domains.list()

        # All domains are valid
        for domain in domains:
            self.check_domain(domain)

        self.assertIn(domain_one.entity, domains)
        self.assertIn(domain_two.entity, domains)

    def test_update_domain(self):
        domain = fixtures.Domain(self.client)
        self.useFixture(domain)

        new_description = uuid.uuid4().hex
        domain_ret = self.client.domains.update(domain.id,
                                                description=new_description)

        domain.ref.update({'description': new_description})
        self.check_domain(domain_ret, domain.ref)

    def test_delete_domain(self):
        domain = self.client.domains.create(name=uuid.uuid4().hex,
                                            description=uuid.uuid4().hex,
                                            enabled=True)

        # Only disabled domains can be deleted
        self.assertRaises(http.Forbidden,
                          self.client.domains.delete,
                          domain.id)

        self.client.domains.update(domain, enabled=False)
        self.client.domains.delete(domain.id)
        self.assertRaises(http.NotFound,
                          self.client.domains.get,
                          domain.id)
