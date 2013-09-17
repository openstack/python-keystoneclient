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

from keystoneclient import exceptions
from keystoneclient.v2_0 import tenants
from tests.v2_0 import utils


class TenantTests(utils.TestCase):
    def setUp(self):
        super(TenantTests, self).setUp()
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
                    },
                    {
                        "extravalue01": "metadata01",
                        "enabled": True,
                        "description": "For testing extras",
                        "name": "test_extras",
                        "id": 4,
                    }
                ],
                "links": [],
            },
        }

    @httpretty.activate
    def test_create(self):
        req_body = {
            "tenant": {
                "name": "tenantX",
                "description": "Like tenant 9, but better.",
                "enabled": True,
                "extravalue01": "metadata01",
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": True,
                "id": 4,
                "description": "Like tenant 9, but better.",
                "extravalue01": "metadata01",
            }
        }
        self.stub_url(httpretty.POST, ['tenants'], json=resp_body)

        tenant = self.client.tenants.create(
            req_body['tenant']['name'],
            req_body['tenant']['description'],
            req_body['tenant']['enabled'],
            extravalue01=req_body['tenant']['extravalue01'],
            name="dont overwrite priors")
        self.assertTrue(isinstance(tenant, tenants.Tenant))
        self.assertEqual(tenant.id, 4)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "Like tenant 9, but better.")
        self.assertEqual(tenant.extravalue01, "metadata01")
        self.assertRequestBodyIs(json=req_body)

    @httpretty.activate
    def test_duplicate_create(self):
        req_body = {
            "tenant": {
                "name": "tenantX",
                "description": "The duplicate tenant.",
                "enabled": True
            },
        }
        resp_body = {
            "error": {
                "message": "Conflict occurred attempting to store project.",
                "code": 409,
                "title": "Conflict",
            }
        }
        self.stub_url(httpretty.POST, ['tenants'], status=409, json=resp_body)

        def create_duplicate_tenant():
            self.client.tenants.create(req_body['tenant']['name'],
                                       req_body['tenant']['description'],
                                       req_body['tenant']['enabled'])

        self.assertRaises(exceptions.Conflict, create_duplicate_tenant)

    @httpretty.activate
    def test_delete(self):
        self.stub_url(httpretty.DELETE, ['tenants', '1'], status=204)
        self.client.tenants.delete(1)

    @httpretty.activate
    def test_get(self):
        resp = {'tenant': self.TEST_TENANTS['tenants']['values'][2]}
        self.stub_url(httpretty.GET, ['tenants', '1'], json=resp)

        t = self.client.tenants.get(1)
        self.assertTrue(isinstance(t, tenants.Tenant))
        self.assertEqual(t.id, 1)
        self.assertEqual(t.name, 'admin')

    @httpretty.activate
    def test_list(self):
        self.stub_url(httpretty.GET, ['tenants'], json=self.TEST_TENANTS)

        tenant_list = self.client.tenants.list()
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    @httpretty.activate
    def test_list_limit(self):
        self.stub_url(httpretty.GET, ['tenants'], json=self.TEST_TENANTS)

        tenant_list = self.client.tenants.list(limit=1)
        self.assertQueryStringIs({'limit': ['1']})
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    @httpretty.activate
    def test_list_marker(self):
        self.stub_url(httpretty.GET, ['tenants'], json=self.TEST_TENANTS)

        tenant_list = self.client.tenants.list(marker=1)
        self.assertQueryStringIs({'marker': ['1']})
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    @httpretty.activate
    def test_list_limit_marker(self):
        self.stub_url(httpretty.GET, ['tenants'], json=self.TEST_TENANTS)

        tenant_list = self.client.tenants.list(limit=1, marker=1)
        self.assertQueryStringIs({'marker': ['1'], 'limit': ['1']})
        [self.assertTrue(isinstance(t, tenants.Tenant)) for t in tenant_list]

    @httpretty.activate
    def test_update(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
                "extravalue01": "metadataChanged",
                #"extraname": "dontoverwrite!",
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": False,
                "id": 4,
                "description": "I changed you!",
                "extravalue01": "metadataChanged",
            },
        }

        self.stub_url(httpretty.POST, ['tenants', '4'], json=resp_body)

        tenant = self.client.tenants.update(
            req_body['tenant']['id'],
            req_body['tenant']['name'],
            req_body['tenant']['description'],
            req_body['tenant']['enabled'],
            extravalue01=req_body['tenant']['extravalue01'],
            name="dont overwrite priors")
        self.assertTrue(isinstance(tenant, tenants.Tenant))
        self.assertRequestBodyIs(json=req_body)
        self.assertEqual(tenant.id, 4)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "I changed you!")
        self.assertFalse(tenant.enabled)
        self.assertEqual(tenant.extravalue01, "metadataChanged")

    @httpretty.activate
    def test_update_empty_description(self):
        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "",
                "enabled": False,
            },
        }
        resp_body = {
            "tenant": {
                "name": "tenantX",
                "enabled": False,
                "id": 4,
                "description": "",
            },
        }
        self.stub_url(httpretty.POST, ['tenants', '4'], json=resp_body)

        tenant = self.client.tenants.update(req_body['tenant']['id'],
                                            req_body['tenant']['name'],
                                            req_body['tenant']['description'],
                                            req_body['tenant']['enabled'])
        self.assertTrue(isinstance(tenant, tenants.Tenant))
        self.assertRequestBodyIs(json=req_body)
        self.assertEqual(tenant.id, 4)
        self.assertEqual(tenant.name, "tenantX")
        self.assertEqual(tenant.description, "")
        self.assertFalse(tenant.enabled)

    @httpretty.activate
    def test_add_user(self):
        self.stub_url(httpretty.PUT, ['tenants', '4', 'users', 'foo', 'roles',
                                      'OS-KSADM', 'barrr'], status=204)

        self.client.tenants.add_user('4', 'foo', 'barrr')

    @httpretty.activate
    def test_remove_user(self):
        self.stub_url(httpretty.DELETE, ['tenants', '4', 'users', 'foo',
                                         'roles', 'OS-KSADM', 'barrr'],
                      status=204)

        self.client.tenants.remove_user('4', 'foo', 'barrr')

    @httpretty.activate
    def test_tenant_add_user(self):
        self.stub_url(httpretty.PUT, ['tenants', '4', 'users', 'foo', 'roles',
                                      'OS-KSADM', 'barrr'],
                      status=204)

        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }
        # make tenant object with manager
        tenant = self.client.tenants.resource_class(self.client.tenants,
                                                    req_body['tenant'])
        tenant.add_user('foo', 'barrr')
        self.assertTrue(isinstance(tenant, tenants.Tenant))

    @httpretty.activate
    def test_tenant_remove_user(self):
        self.stub_url(httpretty.DELETE, ['tenants', '4', 'users', 'foo',
                                         'roles', 'OS-KSADM', 'barrr'],
                      status=204)

        req_body = {
            "tenant": {
                "id": 4,
                "name": "tenantX",
                "description": "I changed you!",
                "enabled": False,
            },
        }

        # make tenant object with manager
        tenant = self.client.tenants.resource_class(self.client.tenants,
                                                    req_body['tenant'])
        tenant.remove_user('foo', 'barrr')
        self.assertTrue(isinstance(tenant, tenants.Tenant))
