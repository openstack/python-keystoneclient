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


class DomainConfigsTestCase(base.V3ClientTestCase):

    def setUp(self):
        super(DomainConfigsTestCase, self).setUp()
        self.test_domain = fixtures.Domain(self.client)
        self.useFixture(self.test_domain)

    def check_domain_config(self, config, config_ref):
        for attr in config_ref:
            self.assertEqual(
                getattr(config, attr),
                config_ref[attr],
                'Expected different %s' % attr)

    def _new_ref(self):
        return {'identity': {'driver': uuid.uuid4().hex},
                'ldap': {'url': uuid.uuid4().hex}}

    def test_create_domain_config(self):
        config_ref = self._new_ref()
        config = self.client.domain_configs.create(
            self.test_domain.id, config_ref)
        self.addCleanup(
            self.client.domain_configs.delete, self.test_domain.id)
        self.check_domain_config(config, config_ref)

    def test_create_invalid_domain_config(self):
        invalid_groups_ref = {
            uuid.uuid4().hex: {uuid.uuid4().hex: uuid.uuid4().hex},
            uuid.uuid4().hex: {uuid.uuid4().hex: uuid.uuid4().hex}}
        self.assertRaises(http.Forbidden,
                          self.client.domain_configs.create,
                          self.test_domain.id,
                          invalid_groups_ref)

        invalid_options_ref = {
            'identity': {uuid.uuid4().hex: uuid.uuid4().hex},
            'ldap': {uuid.uuid4().hex: uuid.uuid4().hex}}
        self.assertRaises(http.Forbidden,
                          self.client.domain_configs.create,
                          self.test_domain.id,
                          invalid_options_ref)

    def test_get_domain_config(self):
        config = fixtures.DomainConfig(self.client, self.test_domain.id)
        self.useFixture(config)

        config_ret = self.client.domain_configs.get(self.test_domain.id)
        self.check_domain_config(config_ret, config.ref)

    def test_update_domain_config(self):
        config = fixtures.DomainConfig(self.client, self.test_domain.id)
        self.useFixture(config)

        update_config_ref = self._new_ref()
        config_ret = self.client.domain_configs.update(
            self.test_domain.id, update_config_ref)
        self.check_domain_config(config_ret, update_config_ref)

    def test_update_invalid_domain_config(self):
        config = fixtures.DomainConfig(self.client, self.test_domain.id)
        self.useFixture(config)

        invalid_groups_ref = {
            uuid.uuid4().hex: {uuid.uuid4().hex: uuid.uuid4().hex},
            uuid.uuid4().hex: {uuid.uuid4().hex: uuid.uuid4().hex}}
        self.assertRaises(http.Forbidden,
                          self.client.domain_configs.update,
                          self.test_domain.id,
                          invalid_groups_ref)

        invalid_options_ref = {
            'identity': {uuid.uuid4().hex: uuid.uuid4().hex},
            'ldap': {uuid.uuid4().hex: uuid.uuid4().hex}}
        self.assertRaises(http.Forbidden,
                          self.client.domain_configs.update,
                          self.test_domain.id,
                          invalid_options_ref)

    def test_domain_config_delete(self):
        config_ref = self._new_ref()
        self.client.domain_configs.create(self.test_domain.id, config_ref)

        self.client.domain_configs.delete(self.test_domain.id)
        self.assertRaises(http.NotFound,
                          self.client.domain_configs.get,
                          self.project_domain_id)
