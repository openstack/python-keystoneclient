import urlparse
import json

import httplib2

from keystoneclient.v2_0 import tenants
from tests import utils


class TenantTests(utils.TestCase):
    def setUp(self):
        super(TenantTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
        }
        self.TEST_POST_HEADERS = {
            'Content-Type': 'application/json',
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
        }
        self.TEST_TENANTS = {
            "tenants": {
                "values": [
                    {
                        "enabled": True,
                        "description": "A description change!",
                        "name": "invisible_to_admin",
                        "id": 3,
                    },
                    {
                        "enabled": True,
                        "description": "None",
                        "name": "demo",
                        "id": 2,
                    },
                    {
                        "enabled": True,
                        "description": "None",
                        "name": "admin",
                        "id": 1,
                    }
                ],
                "links": [],
            },
        }

    def test_create(self):
        req_body = {
            "tenant": {
                "name": "tenantX",
                "description": "Like tenant 9, but better.",
                "enabled": True
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": True,
                "id": 4,
                "description": "Like tenant 9, but better.",
            }
        }
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
        })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL, 'v2.0/tenants'),
                              'POST',
                              body=json.dumps(req_body),
                              headers=self.TEST_POST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        tenant = self.client.tenants.create(req_body['tenant']['name'],
                                            req_body['tenant']['description'],
                                            req_body['tenant']['enabled'])
        self.assertTrue(isinstance(tenant, tenants.Tenant))
        self.assertEqual(tenant.id, 4)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "Like tenant 9, but better.")

    def test_delete(self):
        resp = httplib2.Response({
            "status": 200,
            "body": "",
        })
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants/1'),
                              'DELETE',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.client.tenants.delete(1)

    def test_get(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps({
                'tenant': self.TEST_TENANTS['tenants']['values'][2],
            }),
        })
        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants/1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        t = self.client.tenants.get(1)
        self.assertTrue(isinstance(t, tenants.Tenant))
        self.assertEqual(t.id, 1)
        self.assertEqual(t.name, 'admin')

    def test_list(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_TENANTS),
        })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        tenant_list = self.client.tenants.list()
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    def test_list_limit(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_TENANTS),
        })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants?limit=1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        tenant_list = self.client.tenants.list(limit=1)
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    def test_list_marker(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_TENANTS),
        })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants?marker=1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        tenant_list = self.client.tenants.list(marker=1)
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    def test_list_limit_marker(self):
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(self.TEST_TENANTS),
        })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants?marker=1&limit=1'),
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        tenant_list = self.client.tenants.list(limit=1, marker=1)
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    def test_update(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": False,
                "id": 4,
                "description": "I changed you!",
            },
        }
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
        })

        httplib2.Http.request(urlparse.urljoin(self.TEST_URL,
                              'v2.0/tenants/4'),
                              'POST',
                              body=json.dumps(req_body),
                              headers=self.TEST_POST_HEADERS) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        tenant = self.client.tenants.update(req_body['tenant']['id'],
                                            req_body['tenant']['name'],
                                            req_body['tenant']['description'],
                                            req_body['tenant']['enabled'])
        self.assertTrue(isinstance(tenant, tenants.Tenant))
        self.assertEqual(tenant.id, 4)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "I changed you!")
        self.assertFalse(tenant.enabled)

    def test_add_user(self):
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

        self.client.tenants.add_user('4', 'foo', 'barrr')

    def test_remove_user(self):
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

        self.client.tenants.remove_user('4', 'foo', 'barrr')

    def test_tenant_add_user(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }
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

        # make tenant object with manager
        tenant = self.client.tenants.resource_class(self.client.tenants,
                                                    req_body['tenant'])
        tenant.add_user('foo', 'barrr')
        self.assertTrue(isinstance(tenant, tenants.Tenant))

    def test_tenant_remove_user(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }
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

        # make tenant object with manager
        tenant = self.client.tenants.resource_class(self.client.tenants,
                                                    req_body['tenant'])
        tenant.remove_user('foo', 'barrr')
        self.assertTrue(isinstance(tenant, tenants.Tenant))
