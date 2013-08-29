# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import httpretty

from keystoneclient.v2_0 import roles
from tests.v2_0 import utils


class RoleTests(utils.TestCase):
    def setUp(self):
        super(RoleTests, self).setUp()
        self.TEST_ROLES = {
            "roles": {
                "values": [
                    {
                        "name": "admin",
                        "id": 1,
                    },
                    {
                        "name": "member",
                        "id": 2,
                    }
                ],
            },
        }

    @httpretty.activate
    def test_create(self):
        req_body = {
            "role": {
                "name": "sysadmin",
            }
        }
        resp_body = {
            "role": {
                "name": "sysadmin",
                "id": 3,
            }
        }
        self.stub_url(httpretty.POST, ['OS-KSADM', 'roles'], json=resp_body)

        role = self.client.roles.create(req_body['role']['name'])
        self.assertRequestBodyIs(json=req_body)
        self.assertTrue(isinstance(role, roles.Role))
        self.assertEqual(role.id, 3)
        self.assertEqual(role.name, req_body['role']['name'])

    @httpretty.activate
    def test_delete(self):
        self.stub_url(httpretty.DELETE, ['OS-KSADM', 'roles', '1'], status=204)
        self.client.roles.delete(1)

    @httpretty.activate
    def test_get(self):
        self.stub_url(httpretty.GET, ['OS-KSADM', 'roles', '1'],
                      json={'role': self.TEST_ROLES['roles']['values'][0]})

        role = self.client.roles.get(1)
        self.assertTrue(isinstance(role, roles.Role))
        self.assertEqual(role.id, 1)
        self.assertEqual(role.name, 'admin')

    @httpretty.activate
    def test_list(self):
        self.stub_url(httpretty.GET, ['OS-KSADM', 'roles'],
                      json=self.TEST_ROLES)

        role_list = self.client.roles.list()
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    @httpretty.activate
    def test_roles_for_user(self):
        self.stub_url(httpretty.GET, ['users', 'foo', 'roles'],
                      json=self.TEST_ROLES)

        role_list = self.client.roles.roles_for_user('foo')
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    @httpretty.activate
    def test_roles_for_user_tenant(self):
        self.stub_url(httpretty.GET, ['tenants', 'barrr', 'users', 'foo',
                                      'roles'], json=self.TEST_ROLES)

        role_list = self.client.roles.roles_for_user('foo', 'barrr')
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    @httpretty.activate
    def test_add_user_role(self):
        self.stub_url(httpretty.PUT, ['users', 'foo', 'roles', 'OS-KSADM',
                                      'barrr'], status=204)

        self.client.roles.add_user_role('foo', 'barrr')

    @httpretty.activate
    def test_add_user_role_tenant(self):
        self.stub_url(httpretty.PUT, ['tenants', '4', 'users', 'foo', 'roles',
                                      'OS-KSADM', 'barrr'], status=204)

        self.client.roles.add_user_role('foo', 'barrr', '4')

    @httpretty.activate
    def test_remove_user_role(self):
        self.stub_url(httpretty.DELETE, ['users', 'foo', 'roles', 'OS-KSADM',
                                         'barrr'], status=204)
        self.client.roles.remove_user_role('foo', 'barrr')

    @httpretty.activate
    def test_remove_user_role_tenant(self):
        self.stub_url(httpretty.DELETE, ['tenants', '4', 'users', 'foo',
                                         'roles', 'OS-KSADM', 'barrr'],
                      status=204)
        self.client.roles.remove_user_role('foo', 'barrr', '4')
