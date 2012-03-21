import urlparse
import json

import httplib2

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
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/OS-KSADM/roles'),
                              'POST',
                              body=json.dumps(req_body),
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        role = self.client.roles.create(req_body['role']['name'])
        self.assertTrue(isinstance(role, roles.Role))
        self.assertEqual(role.id, 3)
        self.assertEqual(role.name, req_body['role']['name'])

    def test_delete(self):
        resp = httplib2.Response({
            "status": 200,
            "body": "",
            })
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/OS-KSADM/roles/1'),
                              'DELETE',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.client.roles.delete(1)

    def test_get(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps({
                'role': self.TEST_ROLES['roles']['values'][0],
                }),
            })
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/OS-KSADM/roles/1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        role = self.client.roles.get(1)
        self.assertTrue(isinstance(role, roles.Role))
        self.assertEqual(role.id, 1)
        self.assertEqual(role.name, 'admin')

    def test_list(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_ROLES),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/OS-KSADM/roles'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        role_list = self.client.roles.list()
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    def test_roles_for_user(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_ROLES),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users/foo/roles'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        role_list = self.client.roles.roles_for_user('foo')
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    def test_roles_for_user_tenant(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_ROLES),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants/barrr/users/foo/roles'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        role_list = self.client.roles.roles_for_user('foo', 'barrr')
        [self.assertTrue(isinstance(r, roles.Role)) for r in role_list]

    def test_add_user_role(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps({}),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users/foo/roles/OS-KSADM/barrr'),
                              'PUT',
                              body='null',
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp, None))
        self.mox.ReplayAll()

        self.client.roles.add_user_role('foo', 'barrr')

    def test_add_user_role_tenant(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps({}),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants/4/users/foo/roles/OS-KSADM/barrr'),
                              'PUT',
                              body='null',
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp, None))
        self.mox.ReplayAll()

        self.client.roles.add_user_role('foo', 'barrr', '4')

    def test_remove_user_role(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps({}),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users/foo/roles/OS-KSADM/barrr'),
                              'DELETE',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, None))
        self.mox.ReplayAll()

        self.client.roles.remove_user_role('foo', 'barrr')

    def test_remove_user_role_tenant(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps({}),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants/4/users/foo/roles/OS-KSADM/barrr'),
                              'DELETE',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, None))
        self.mox.ReplayAll()

        self.client.roles.remove_user_role('foo', 'barrr', '4')
