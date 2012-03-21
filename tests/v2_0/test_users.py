import urlparse
import json

import httplib2

from keystoneclient.v2_0 import users
from tests import utils


class UserTests(utils.TestCase):
    def setUp(self):
        super(UserTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
            }
        self.TEST_POST_HEADERS = {
            'Content-Type': 'application/json',
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
            }
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
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL, 'v2.0/users'),
                              'POST',
                              body=json.dumps(req_body),
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        user = self.client.users.create(req_body['user']['name'],
                                        req_body['user']['password'],
                                        req_body['user']['email'],
                                        tenant_id=req_body['user']['tenantId'],
                                        enabled=req_body['user']['enabled'])
        self.assertTrue(isinstance(user, users.User))
        self.assertEqual(user.id, 3)
        self.assertEqual(user.name, "gabriel")
        self.assertEqual(user.email, "test@example.com")

    def test_delete(self):
        resp = httplib2.Response({
            "status": 200,
            "body": "",
            })
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL, 'v2.0/users/1'),
                              'DELETE',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.client.users.delete(1)

    def test_get(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps({
                'user': self.TEST_USERS['users']['values'][0],
                })
            })
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users/1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        u = self.client.users.get(1)
        self.assertTrue(isinstance(u, users.User))
        self.assertEqual(u.id, 1)
        self.assertEqual(u.name, 'admin')

    def test_list(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_USERS),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        user_list = self.client.users.list()
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    def test_list_limit(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_USERS),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users?limit=1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        user_list = self.client.users.list(limit=1)
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    def test_list_marker(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_USERS),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users?marker=1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        user_list = self.client.users.list(marker=1)
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    def test_list_limit_marker(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_USERS),
            })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users?marker=1&limit=1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        user_list = self.client.users.list(limit=1, marker=1)
        [self.assertTrue(isinstance(u, users.User)) for u in user_list]

    def test_update(self):
        req_1 = {"user": {"password": "swordfish", "id": 2}}
        req_2 = {"user": {"id": 2,
                          "email": "gabriel@example.com",
                          "name": "gabriel"}}
        req_3 = {"user": {"tenantId": 1, "id": 2}}
        req_4 = {"user": {"enabled": False, "id": 2}}
        # Keystone basically echoes these back... including the password :-/
        resp_1 = httplib2.Response({"status": 200, "body": json.dumps(req_1)})
        resp_2 = httplib2.Response({"status": 200, "body": json.dumps(req_2)})
        resp_3 = httplib2.Response({"status": 200, "body": json.dumps(req_3)})
        resp_4 = httplib2.Response({"status": 200, "body": json.dumps(req_3)})

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL, 'v2.0/users/2'),
                              'PUT',
                              body=json.dumps(req_2),
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp_2, resp_2['body']))
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users/2/OS-KSADM/password'),
                              'PUT',
                              body=json.dumps(req_1),
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp_1, resp_1['body']))
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users/2/OS-KSADM/tenant'),
                              'PUT',
                              body=json.dumps(req_3),
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp_3, resp_3['body']))
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/users/2/OS-KSADM/enabled'),
                              'PUT',
                              body=json.dumps(req_4),
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp_4, resp_4['body']))
        self.mox.ReplayAll()

        user = self.client.users.update(2,
                                        name='gabriel',
                                        email='gabriel@example.com')
        user = self.client.users.update_password(2, 'swordfish')
        user = self.client.users.update_tenant(2, 1)
        user = self.client.users.update_enabled(2, False)
