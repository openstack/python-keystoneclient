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

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import domain_configs


class DomainConfigsTests(utils.ClientTestCase, utils.CrudTests):
    """Test domain config database management."""

    def setUp(self):
        super(DomainConfigsTests, self).setUp()
        self.key = 'config'
        self.model = domain_configs.DomainConfig
        self.manager = self.client.domain_configs

    def new_ref(self, **kwargs):
        config_groups = {'identity': {uuid.uuid4().hex: uuid.uuid4().hex},
                         'ldap': {uuid.uuid4().hex: uuid.uuid4().hex}}
        kwargs.setdefault('config', config_groups)
        return kwargs

    def _assert_resource_attributes(self, resource, req_ref):
        for attr in req_ref:
            self.assertEqual(
                getattr(resource, attr),
                req_ref[attr],
                'Expected different %s' % attr)

    def test_create(self):
        domain_id = uuid.uuid4().hex
        config = self.new_ref()

        self.stub_url('PUT',
                      parts=['domains', domain_id, 'config'],
                      json=config, status_code=201)
        res = self.manager.create(domain_id, config)
        self._assert_resource_attributes(res, config['config'])
        self.assertEntityRequestBodyIs(config)

    def test_update(self):
        domain_id = uuid.uuid4().hex
        config = self.new_ref()

        self.stub_url('PATCH',
                      parts=['domains', domain_id, 'config'],
                      json=config, status_code=200)
        res = self.manager.update(domain_id, config)
        self._assert_resource_attributes(res, config['config'])
        self.assertEntityRequestBodyIs(config)

    def test_get(self):
        domain_id = uuid.uuid4().hex
        config = self.new_ref()
        config = config['config']

        self.stub_entity('GET',
                         parts=['domains', domain_id, 'config'],
                         entity=config)
        res = self.manager.get(domain_id)
        self._assert_resource_attributes(res, config)

    def test_delete(self):
        domain_id = uuid.uuid4().hex
        self.stub_url('DELETE',
                      parts=['domains', domain_id, 'config'],
                      status_code=204)
        self.manager.delete(domain_id)

    def test_list(self):
        # List not supported for domain config
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.list)

    def test_list_by_id(self):
        # List not supported for domain config
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.list)

    def test_list_params(self):
        # List not supported for domain config
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.list)

    def test_find(self):
        # Find not supported for domain config
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.find)
