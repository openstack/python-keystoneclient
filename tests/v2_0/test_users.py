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

from keystoneclient.v2_0 import users
from tests.v2_0 import utils


class UserTests(utils.TestCase):
    def setUp(self):
        super(UserTests, self).setUp()
        self.TEST_USERS = {
            "users": {
                "values": [
                    {
                        "email": "None",
                        "enabled": True,
                        "id": 1,
                        "name": "admin",
                    },
                    {
                        "email": "None",
                        "enabled": True,
                        "id": 2,
                        "name": "demo",
                    },
                ]
            }
        }

    @httpretty.activate
    def test_create(self):
        req_body = {
            "user": {
                "name": "gabriel",
                "password": "test",
                "tenantId": 2,
                "email": "test@example.com",
                "enabled": True,
            }
        }

        resp_body = {
            "user": {
                "name": "gabriel",
                "enabled": True,
                "tenantId": 2,
                "id": 3,
                "password": "test",
                "email": "test@example.com",
            }
        }

        self.stub_url(httpretty.POST, ['users'], json=resp_body)

        user = self.client.users.create(req_body['user']['name'],
                                        req_body['user']['password'],
                                        req_body['user']['email'],
                                        tenant_id=req_body['user']['tenantId'],
                                        enabled=req_body['user']['enabled'])
        self.assertTrue(isinstance(user, users.User))
        self.assertEqual(user.id, 3)
        self.assertEqual(user.name, "gabriel")
        self.assertEqual(user.email, "test@example.com")
        self.assertRequestBodyIs(json=req_body)

    @httpretty.activate
    def test_delete(self):
        self.stub_url(httpretty.DELETE, ['users', '1'], status=204)
        self.client.users.delete(1)

    @httpretty.activate
    def test_get(self):
        self.stub_url(httpretty.GET, ['users', '1'],
                      json={'user': self.TEST_USERS['users']['values'][0]})

        u = self.client.users.get(1)
        self.assertTrue(isinstance(u, users.User))
        self.assertEqual(u.id, 1)
        self.assertEqual(u.name, 'admin')

    @httpretty.activate
    def test_list(self):
        self.stub_url(httpretty.GET, ['users'], json=self.TEST_USERS)

        user_list = self.client.users.list()
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    @httpretty.activate
    def test_list_limit(self):
        self.stub_url(httpretty.GET, ['users'], json=self.TEST_USERS)

        user_list = self.client.users.list(limit=1)
        self.assertEqual(httpretty.last_request().querystring,
                         {'limit': ['1']})
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    @httpretty.activate
    def test_list_marker(self):
        self.stub_url(httpretty.GET, ['users'], json=self.TEST_USERS)

        user_list = self.client.users.list(marker='foo')
        self.assertDictEqual(httpretty.last_request().querystring,
                             {'marker': ['foo']})
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    @httpretty.activate
    def test_list_limit_marker(self):
        self.stub_url(httpretty.GET, ['users'], json=self.TEST_USERS)

        user_list = self.client.users.list(limit=1, marker='foo')

        self.assertDictEqual(httpretty.last_request().querystring,
                             {'marker': ['foo'], 'limit': ['1']})
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    @httpretty.activate
    def test_update(self):
        req_1 = {
            "user": {
                "id": 2,
                "email": "gabriel@example.com",
                "name": "gabriel",
            }
        }
        req_2 = {
            "user": {
                "id": 2,
                "password": "swordfish",
            }
        }
        req_3 = {
            "user": {
                "id": 2,
                "tenantId": 1,
            }
        }
        req_4 = {
            "user": {
                "id": 2,
                "enabled": False,
            }
        }

        self.stub_url(httpretty.PUT, ['users', '2'], json=req_1)
        self.stub_url(httpretty.PUT, ['users', '2', 'OS-KSADM', 'password'],
                      json=req_2)
        self.stub_url(httpretty.PUT, ['users', '2', 'OS-KSADM', 'tenant'],
                      json=req_3)
        self.stub_url(httpretty.PUT, ['users', '2', 'OS-KSADM', 'enabled'],
                      json=req_4)

        self.client.users.update(2,
                                 name='gabriel',
                                 email='gabriel@example.com')
        self.assertRequestBodyIs(json=req_1)
        self.client.users.update_password(2, 'swordfish')
        self.assertRequestBodyIs(json=req_2)
        self.client.users.update_tenant(2, 1)
        self.assertRequestBodyIs(json=req_3)
        self.client.users.update_enabled(2, False)
        self.assertRequestBodyIs(json=req_4)

    @httpretty.activate
    def test_update_own_password(self):
        req_body = {
            'user': {
                'password': 'ABCD', 'original_password': 'DCBA'
            }
        }
        resp_body = {
            'access': {}
        }
        self.stub_url(httpretty.PATCH, ['OS-KSCRUD', 'users', '123'],
                      json=resp_body)

        self.client.user_id = '123'
        self.client.users.update_own_password('DCBA', 'ABCD')
        self.assertRequestBodyIs(json=req_body)
