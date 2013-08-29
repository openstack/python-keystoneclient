# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import urlparse

from tests import fakes
from tests.v2_0 import utils


class FakeHTTPClient(fakes.FakeClient):
    def __init__(self, **kwargs):
        self.username = 'username'
        self.password = 'password'
        self.auth_url = 'auth_url'
        self.callstack = []

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method == 'PUT':
            kwargs.setdefault('body', None)

        # Call the method
        args = urlparse.parse_qsl(urlparse.urlparse(url)[4])
        kwargs.update(args)
        munged_url = url.rsplit('?', 1)[0]
        munged_url = munged_url.strip('/').replace('/', '_').replace('.', '_')
        munged_url = munged_url.replace('-', '_')

        callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body', None)))

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body', None)))

        status, body = getattr(self, callback)(**kwargs)
        r = utils.TestResponse({
            "status_code": status,
            "text": body})
        return r, body

    #
    # List all extensions
    #
    def post_tokens(self, **kw):
        body = [
            {"access":
                {"token":
                    {"expires": "2012-02-05T00:00:00",
                     "id": "887665443383838",
                     "tenant":
                        {"id": "1",
                         "name": "customer-x"}},
                 "serviceCatalog": [
                    {"endpoints": [
                        {"adminURL": "http://swift.admin-nets.local:8080/",
                         "region": "RegionOne",
                         "internalURL": "http://127.0.0.1:8080/v1/AUTH_1",
                         "publicURL":
                         "http://swift.publicinternets.com/v1/AUTH_1"}],
                     "type": "object-store",
                     "name": "swift"},
                    {"endpoints": [
                        {"adminURL": "http://cdn.admin-nets.local/v1.1/1",
                         "region": "RegionOne",
                         "internalURL": "http://127.0.0.1:7777/v1.1/1",
                         "publicURL":
                         "http://cdn.publicinternets.com/v1.1/1"}],
                     "type": "object-store",
                     "name": "cdn"}],
                 "user":
                    {"id": "1",
                     "roles": [
                         {"tenantId": "1",
                          "id": "3",
                          "name": "Member"}],
                 "name": "joeuser"}}
             }
        ]
        return (200, body)

    def get_tokens_887665443383838(self, **kw):
        body = [
            {"access":
                {"token":
                    {"expires": "2012-02-05T00:00:00",
                     "id": "887665443383838",
                     "tenant": {"id": "1",
                                "name": "customer-x"}},
                 "user":
                 {"name": "joeuser",
                  "tenantName": "customer-x",
                  "id": "1",
                  "roles": [
                  {"serviceId": "1",
                          "id": "3",
                          "name": "Member"}],
                 "tenantId": "1"}}
             }
        ]
        return (200, body)

    def get_tokens_887665443383838_endpoints(self, **kw):
        body = [
            {"endpoints_links": [
                {"href":
                 "http://127.0.0.1:35357/tokens/887665443383838"
                 "/endpoints?'marker=5&limit=10'",
                 "rel": "next"}],
             "endpoints": [
                 {"internalURL": "http://127.0.0.1:8080/v1/AUTH_1",
                  "name": "swift",
                  "adminURL": "http://swift.admin-nets.local:8080/",
                  "region": "RegionOne",
                  "tenantId": 1,
                  "type": "object-store",
                  "id": 1,
                  "publicURL": "http://swift.publicinternets.com/v1/AUTH_1"},
                 {"internalURL": "http://localhost:8774/v1.0",
                  "name": "nova_compat",
                  "adminURL": "http://127.0.0.1:8774/v1.0",
                  "region": "RegionOne",
                  "tenantId": 1,
                  "type": "compute",
                  "id": 2,
                  "publicURL": "http://nova.publicinternets.com/v1.0/"},
                 {"internalURL": "http://localhost:8774/v1.1",
                  "name": "nova",
                  "adminURL": "http://127.0.0.1:8774/v1.1",
                  "region": "RegionOne",
                  "tenantId": 1,
                  "type": "compute",
                  "id": 3,
                  "publicURL": "http://nova.publicinternets.com/v1.1/"},
                 {"internalURL": "http://127.0.0.1:9292/v1.1/",
                  "name": "glance",
                  "adminURL": "http://nova.admin-nets.local/v1.1/",
                  "region": "RegionOne",
                  "tenantId": 1,
                  "type": "image",
                  "id": 4,
                  "publicURL": "http://glance.publicinternets.com/v1.1/"},
                 {"internalURL": "http://127.0.0.1:7777/v1.1/1",
                  "name": "cdn",
                  "adminURL": "http://cdn.admin-nets.local/v1.1/1",
                  "region": "RegionOne",
                  "tenantId": 1,
                  "versionId": "1.1",
                  "versionList": "http://127.0.0.1:7777/",
                  "versionInfo": "http://127.0.0.1:7777/v1.1",
                  "type": "object-store",
                  "id": 5,
                  "publicURL": "http://cdn.publicinternets.com/v1.1/1"}]
             }
        ]
        return (200, body)

    def get(self, **kw):
        body = {
            "version": {
            "id": "v2.0",
            "status": "beta",
            "updated": "2011-11-19T00:00:00Z",
            "links": [
                {"rel": "self",
                 "href": "http://127.0.0.1:35357/v2.0/"},
                {"rel": "describedby",
                 "type": "text/html",
                 "href": "http://docs.openstack.org/"
                         "api/openstack-identity-service/2.0/content/"},
                {"rel": "describedby",
                 "type": "application/pdf",
                 "href": "http://docs.openstack.org/api/"
                 "openstack-identity-service/2.0/identity-dev-guide-2.0.pdf"},
                {"rel": "describedby",
                 "type": "application/vnd.sun.wadl+xml",
                 "href": "http://127.0.0.1:35357/v2.0/identity-admin.wadl"}],
            "media-types": [
                {"base": "application/xml",
                 "type": "application/vnd.openstack.identity-v2.0+xml"},
                {"base": "application/json",
                 "type": "application/vnd.openstack.identity-v2.0+json"}]
            }
        }
        return (200, body)

    def get_extensions(self, **kw):
        body = {
            "extensions": {"values": []}
        }
        return (200, body)

    def post_tenants(self, **kw):
        body = {"tenant":
               {"enabled": True,
                "description": None,
                "name": "new-tenant",
                "id": "1"}}
        return (200, body)

    def post_tenants_2(self, **kw):
        body = {"tenant":
               {"enabled": False,
                "description": "desc",
                "name": "new-tenant1",
                "id": "2"}}
        return (200, body)

    def get_tenants(self, **kw):
        body = {
            "tenants_links": [],
            "tenants": [
                {"enabled": False,
                 "description": None,
                 "name": "project-y",
                 "id": "1"},
                {"enabled": True,
                 "description": None,
                 "name": "new-tenant",
                 "id": "2"},
                {"enabled": True,
                 "description": None,
                 "name": "customer-x",
                 "id": "1"}]
        }
        return (200, body)

    def get_tenants_1(self, **kw):
        body = {"tenant":
               {"enabled": True,
                "description": None,
                "name": "new-tenant",
                "id": "1"}}
        return (200, body)

    def get_tenants_2(self, **kw):
        body = {"tenant":
               {"enabled": True,
                "description": None,
                "name": "new-tenant",
                "id": "2"}}
        return (200, body)

    def delete_tenants_2(self, **kw):
        body = {}
        return (200, body)

    def get_tenants_1_users_1_roles(self, **kw):
        body = {
            "roles": [
                {"id": "1",
                 "name": "Admin"},
                {"id": "2",
                 "name": "Member"},
                {"id": "3",
                 "name": "new-role"}]
        }
        return (200, body)

    def put_users_1_roles_OS_KSADM_1(self, **kw):
        body = {
            "roles":
            {"id": "1",
             "name": "Admin"}}
        return (200, body)

    def delete_users_1_roles_OS_KSADM_1(self, **kw):
        body = {}
        return (200, body)

    def put_tenants_1_users_1_roles_OS_KSADM_1(self, **kw):
        body = {
            "role":
            {"id": "1",
             "name": "Admin"}}
        return (200, body)

    def get_users(self, **kw):
        body = {
            "users": [
                {"name": self.username,
                 "enabled": "true",
                 "email": "sdfsdf@sdfsd.sdf",
                 "id": "1",
                 "tenantId": "1"},
                {"name": "user2",
                 "enabled": "true",
                 "email": "sdfsdf@sdfsd.sdf",
                 "id": "2",
                 "tenantId": "1"}]
        }
        return (200, body)

    def get_users_1(self, **kw):
        body = {
            "user": {
                "tenantId": "1",
                "enabled": "true",
                "id": "1",
                "name": self.username}
        }
        return (200, body)

    def put_users_1(self, **kw):
        body = {
            "user": {
                "tenantId": "1",
                "enabled": "true",
                "id": "1",
                "name": "new-user1",
                "email": "user@email.com"}
        }
        return (200, body)

    def put_users_1_OS_KSADM_password(self, **kw):
        body = {
            "user": {
                "tenantId": "1",
                "enabled": "true",
                "id": "1",
                "name": "new-user1",
                "email": "user@email.com"}
        }
        return (200, body)

    def post_users(self, **kw):
        body = {
            "user": {
                "tenantId": "1",
                "enabled": "true",
                "id": "1",
                "name": self.username}
        }
        return (200, body)

    def delete_users_1(self, **kw):
        body = []
        return (200, body)

    def get_users_1_roles(self, **kw):
        body = [
            {"roles_links": [],
             "roles":[
                 {"id": "2",
                  "name": "KeystoneServiceAdmin"}]
             }
        ]
        return (200, body)

    def post_OS_KSADM_roles(self, **kw):
        body = {"role":
               {"name": "new-role",
                "id": "1"}}
        return (200, body)

    def get_OS_KSADM_roles(self, **kw):
        body = {"roles": [
                {"id": "10", "name": "admin"},
                {"id": "20", "name": "member"},
                {"id": "1", "name": "new-role"}]
                }
        return (200, body)

    def get_OS_KSADM_roles_1(self, **kw):
        body = {"role":
               {"name": "new-role",
                "id": "1"}
                }
        return (200, body)

    def delete_OS_KSADM_roles_1(self, **kw):
        body = {}
        return (200, body)

    def post_OS_KSADM_services(self, **kw):
        body = {"OS-KSADM:service":
               {"id": "1",
                "type": "compute",
                "name": "service1",
                "description": None}
                }
        return (200, body)

    def get_OS_KSADM_services_1(self, **kw):
        body = {"OS-KSADM:service":
               {"description": None,
                "type": "compute",
                "id": "1",
                "name": "service1"}
                }
        return (200, body)

    def get_OS_KSADM_services(self, **kw):
        body = {
            "OS-KSADM:services": [
            {"description": None,
             "type": "compute",
             "id": "1",
             "name": "service1"},
            {"description": None,
             "type": "identity",
             "id": "2",
             "name": "service2"}]
        }
        return (200, body)

    def delete_OS_KSADM_services_1(self, **kw):
        body = {}
        return (200, body)

    def post_users_1_credentials_OS_EC2(self, **kw):
        body = {"credential":
               {"access": "1",
                "tenant_id": "1",
                "secret": "1",
                "user_id": "1"}
                }
        return (200, body)

    def get_users_1_credentials_OS_EC2(self, **kw):
        body = {"credentials": [
            {"access": "1",
             "tenant_id": "1",
             "secret": "1",
             "user_id": "1"}]
        }
        return (200, body)

    def get_users_1_credentials_OS_EC2_2(self, **kw):
        body = {
            "credential":
               {"access": "2",
                "tenant_id": "1",
                "secret": "1",
                "user_id": "1"}
        }
        return (200, body)

    def delete_users_1_credentials_OS_EC2_2(self, **kw):
        body = {}
        return (200, body)

    def patch_OS_KSCRUD_users_1(self, **kw):
        body = {}
        return (200, body)

    def get_endpoints(self, **kw):
        body = {
            'endpoints': [
                {'adminURL': 'http://cdn.admin-nets.local/v1.1/1',
                 'region': 'RegionOne',
                 'internalURL': 'http://127.0.0.1:7777/v1.1/1',
                 'publicURL': 'http://cdn.publicinternets.com/v1.1/1'}],
            'type': 'compute',
            'name': 'nova-compute'
        }
        return (200, body)

    def post_endpoints(self, **kw):
        body = {
            "endpoint":
               {"adminURL": "http://swift.admin-nets.local:8080/",
                "region": "RegionOne",
                "internalURL": "http://127.0.0.1:8080/v1/AUTH_1",
                "publicURL": "http://swift.publicinternets.com/v1/AUTH_1"},
            "type": "compute",
            "name": "nova-compute"
        }
        return (200, body)
