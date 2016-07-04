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


class ServicesTestCase(base.V3ClientTestCase):

    def check_service(self, service, service_ref=None):
        self.assertIsNotNone(service.id)
        self.assertIn('self', service.links)
        self.assertIn('/services/' + service.id, service.links['self'])

        if service_ref:
            self.assertEqual(service_ref['name'], service.name)
            self.assertEqual(service_ref['enabled'], service.enabled)
            self.assertEqual(service_ref['type'], service.type)

            # There is no guarantee description is present in service
            if hasattr(service_ref, 'description'):
                self.assertEqual(service_ref['description'],
                                 service.description)

        else:
            # Only check remaining mandatory attributes
            self.assertIsNotNone(service.name)
            self.assertIsNotNone(service.enabled)
            self.assertIsNotNone(service.type)

    def test_create_service(self):
        service_ref = {
            'name': fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex,
            'type': uuid.uuid4().hex,
            'enabled': True,
            'description': uuid.uuid4().hex}

        service = self.client.services.create(**service_ref)

        self.addCleanup(self.client.services.delete, service)
        self.check_service(service, service_ref)

    def test_get_service(self):
        service = fixtures.Service(self.client)
        self.useFixture(service)

        service_ret = self.client.services.get(service.id)
        self.check_service(service_ret, service.ref)

    def test_list_services(self):
        service_one = fixtures.Service(self.client)
        self.useFixture(service_one)

        service_two = fixtures.Service(self.client)
        self.useFixture(service_two)

        services = self.client.services.list()

        # All services are valid
        for service in services:
            self.check_service(service)

        self.assertIn(service_one.entity, services)
        self.assertIn(service_two.entity, services)

    def test_update_service(self):
        service = fixtures.Service(self.client)
        self.useFixture(service)

        new_name = fixtures.RESOURCE_NAME_PREFIX + uuid.uuid4().hex
        new_type = uuid.uuid4().hex
        new_enabled = False
        new_description = uuid.uuid4().hex

        service_ret = self.client.services.update(service.id,
                                                  name=new_name,
                                                  type=new_type,
                                                  enabled=new_enabled,
                                                  description=new_description)

        service.ref.update({'name': new_name, 'type': new_type,
                            'enabled': new_enabled,
                            'description': new_description})
        self.check_service(service_ret, service.ref)

    def test_delete_service(self):
        service = self.client.services.create(name=uuid.uuid4().hex,
                                              type=uuid.uuid4().hex)

        self.client.services.delete(service.id)
        self.assertRaises(http.NotFound,
                          self.client.services.get,
                          service.id)
