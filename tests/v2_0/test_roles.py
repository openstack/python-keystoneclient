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

import copy
import json
import urlparse

import requests

from keystoneclient.v2_0 import roles
from tests import utils


class RoleTests(utils.TestCase):
    def setUp(self):
        super(RoleTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
        }
        self.TEST_POST_HEADERS = {
            'Content-Type': 'application/json',
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
        }
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
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        requests.request('POST',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/OS-KSADM/roles'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        role = self.client.roles.create(req_body['role']['name'])
        self.assertTrue(isinstance(role, roles.Role))
        self.assertEqual(role.id, 3)
        self.assertEqual(role.name, req_body['role']['name'])

    def test_delete(self):
        resp = utils.TestResponse({
            "status_code": 204,
            "text": "",
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('DELETE',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/OS-KSADM/roles/1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.roles.delete(1)

    def test_get(self):
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps({
                'role': self.TEST_ROLES['roles']['values'][0],
            }),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/OS-KSADM/roles/1'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        role = self.client.roles.get(1)
        self.assertTrue(isinstance(role, roles.Role))
        self.assertEqual(role.id, 1)
        self.assertEqual(role.name, 'admin')

    def test_list(self):
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_ROLES),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/OS-KSADM/roles'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        role_list = self.client.roles.list()
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    def test_roles_for_user(self):
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_ROLES),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/users/foo/roles'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        role_list = self.client.roles.roles_for_user('foo')
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    def test_roles_for_user_tenant(self):
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(self.TEST_ROLES),
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('GET',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/barrr/users/foo/roles'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        role_list = self.client.roles.roles_for_user('foo', 'barrr')
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    def test_add_user_role(self):
        resp = utils.TestResponse({
            "status_code": 204,
            "text": '',
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('PUT',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/users/foo/roles/OS-KSADM/barrr'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.roles.add_user_role('foo', 'barrr')

    def test_add_user_role_tenant(self):
        resp = utils.TestResponse({
            "status_code": 204,
            "text": '',
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('PUT',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/4/users/foo/roles/OS-KSADM/barrr'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.roles.add_user_role('foo', 'barrr', '4')

    def test_remove_user_role(self):
        resp = utils.TestResponse({
            "status_code": 204,
            "text": '',
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('DELETE',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/users/foo/roles/OS-KSADM/barrr'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.roles.remove_user_role('foo', 'barrr')

    def test_remove_user_role_tenant(self):
        resp = utils.TestResponse({
            "status_code": 204,
            "text": '',
        })

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('DELETE',
                         urlparse.urljoin(self.TEST_URL,
                         'v2.0/tenants/4/users/foo/roles/OS-KSADM/barrr'),
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.roles.remove_user_role('foo', 'barrr', '4')
