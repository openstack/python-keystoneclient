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

import cStringIO
import os
import sys

from mox3 import stubout
from testtools import matchers

from keystoneclient import httpclient

from tests.v2_0 import fakes
from tests.v2_0 import utils


DEFAULT_USERNAME = 'username'
DEFAULT_PASSWORD = 'password'
DEFAULT_TENANT_ID = 'tenant_id'
DEFAULT_TENANT_NAME = 'tenant_name'
DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/v2.0/'


class ShellTests(utils.TestCase):

    def setUp(self):
        """Patch os.environ to avoid required auth info."""

        super(ShellTests, self).setUp()
        self.stubs = stubout.StubOutForTesting()

        self.fake_client = fakes.FakeHTTPClient()
        self.stubs.Set(
            httpclient.HTTPClient, "_cs_request",
            lambda ign_self, *args, **kwargs:
            self.fake_client._cs_request(*args, **kwargs))
        self.stubs.Set(
            httpclient.HTTPClient, "authenticate",
            lambda cl_obj:
            self.fake_client.authenticate(cl_obj))
        self.old_environment = os.environ.copy()
        os.environ = {
            'OS_USERNAME': DEFAULT_USERNAME,
            'OS_PASSWORD': DEFAULT_PASSWORD,
            'OS_TENANT_ID': DEFAULT_TENANT_ID,
            'OS_TENANT_NAME': DEFAULT_TENANT_NAME,
            'OS_AUTH_URL': DEFAULT_AUTH_URL,
        }
        import keystoneclient.shell
        self.shell = keystoneclient.shell.OpenStackIdentityShell()

    def tearDown(self):
        self.stubs.UnsetAll()
        self.stubs.SmartUnsetAll()
        os.environ = self.old_environment
        self.fake_client.clear_callstack()
        super(ShellTests, self).tearDown()

    def run_command(self, cmd):
        orig = sys.stdout
        try:
            sys.stdout = cStringIO.StringIO()
            self.shell.main(cmd.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(exc_value.code, 0)
        finally:
            out = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig
        return out

    def assert_called(self, method, url, body=None, **kwargs):
        return self.fake_client.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.fake_client.assert_called_anytime(method, url, body)

    def test_user_list(self):
        self.run_command('user-list')
        self.fake_client.assert_called_anytime('GET', '/users')

    def test_user_create(self):
        self.run_command('user-create --name new-user')
        self.fake_client.assert_called_anytime(
            'POST', '/users',
            {'user':
                {'email': None,
                 'password': None,
                 'enabled': True,
                 'name': 'new-user',
                 'tenantId': None}})

    def test_user_get(self):
        self.run_command('user-get 1')
        self.fake_client.assert_called_anytime('GET', '/users/1')

    def test_user_delete(self):
        self.run_command('user-delete 1')
        self.fake_client.assert_called_anytime('DELETE', '/users/1')

    def test_user_password_update(self):
        self.run_command('user-password-update --pass newpass 1')
        self.fake_client.assert_called_anytime(
            'PUT', '/users/1/OS-KSADM/password')

    def test_user_update(self):
        self.run_command('user-update --name new-user1'
                         ' --email user@email.com --enabled true 1')
        self.fake_client.assert_called_anytime(
            'PUT', '/users/1',
            {'user':
                {'id': '1',
                 'email': 'user@email.com',
                 'enabled': True,
                 'name': 'new-user1'}
             })
        required = 'User not updated, no arguments present.'
        out = self.run_command('user-update 1')
        self.assertThat(out, matchers.MatchesRegex(required))

    def test_role_create(self):
        self.run_command('role-create --name new-role')
        self.fake_client.assert_called_anytime(
            'POST', '/OS-KSADM/roles',
            {"role": {"name": "new-role"}})

    def test_role_get(self):
        self.run_command('role-get 1')
        self.fake_client.assert_called_anytime('GET', '/OS-KSADM/roles/1')

    def test_role_list(self):
        self.run_command('role-list')
        self.fake_client.assert_called_anytime('GET', '/OS-KSADM/roles')

    def test_role_delete(self):
        self.run_command('role-delete 1')
        self.fake_client.assert_called_anytime('DELETE', '/OS-KSADM/roles/1')

    def test_user_role_add(self):
        self.run_command('user-role-add --user_id 1 --role_id 1')
        self.fake_client.assert_called_anytime(
            'PUT', '/users/1/roles/OS-KSADM/1')

    def test_user_role_list(self):
        self.run_command('user-role-list --user_id 1 --tenant-id 1')
        self.fake_client.assert_called_anytime(
            'GET', '/tenants/1/users/1/roles')
        self.run_command('user-role-list --user_id 1')
        self.fake_client.assert_called_anytime(
            'GET', '/tenants/1/users/1/roles')
        self.run_command('user-role-list')
        self.fake_client.assert_called_anytime(
            'GET', '/tenants/1/users/1/roles')

    def test_user_role_remove(self):
        self.run_command('user-role-remove --user_id 1 --role_id 1')
        self.fake_client.assert_called_anytime(
            'DELETE', '/users/1/roles/OS-KSADM/1')

    def test_tenant_create(self):
        self.run_command('tenant-create --name new-tenant')
        self.fake_client.assert_called_anytime(
            'POST', '/tenants',
            {"tenant": {"enabled": True,
                        "name": "new-tenant",
                        "description": None}})

    def test_tenant_get(self):
        self.run_command('tenant-get 2')
        self.fake_client.assert_called_anytime('GET', '/tenants/2')

    def test_tenant_list(self):
        self.run_command('tenant-list')
        self.fake_client.assert_called_anytime('GET', '/tenants')

    def test_tenant_update(self):
        self.run_command('tenant-update'
                         ' --name new-tenant1 --enabled false'
                         ' --description desc 2')
        self.fake_client.assert_called_anytime(
            'POST', '/tenants/2',
            {"tenant":
                {"enabled": False,
                 "id": "2",
                 "description": "desc",
                 "name": "new-tenant1"}})

        required = 'Tenant not updated, no arguments present.'
        out = self.run_command('tenant-update 1')
        self.assertThat(out, matchers.MatchesRegex(required))

    def test_tenant_delete(self):
        self.run_command('tenant-delete 2')
        self.fake_client.assert_called_anytime('DELETE', '/tenants/2')

    def test_service_create(self):
        self.run_command('service-create --name service1 --type compute')
        self.fake_client.assert_called_anytime(
            'POST', '/OS-KSADM/services',
            {"OS-KSADM:service":
                {"type": "compute",
                 "name": "service1",
                 "description": None}})

    def test_service_get(self):
        self.run_command('service-get 1')
        self.fake_client.assert_called_anytime('GET', '/OS-KSADM/services/1')

    def test_service_list(self):
        self.run_command('service-list')
        self.fake_client.assert_called_anytime('GET', '/OS-KSADM/services')

    def test_service_delete(self):
        self.run_command('service-delete 1')
        self.fake_client.assert_called_anytime(
            'DELETE', '/OS-KSADM/services/1')

    def test_catalog(self):
        self.run_command('catalog')
        self.run_command('catalog --service compute')

    def test_ec2_credentials_create(self):
        self.run_command('ec2-credentials-create'
                         ' --tenant-id 1 --user-id 1')
        self.fake_client.assert_called_anytime(
            'POST', '/users/1/credentials/OS-EC2',
            {'tenant_id': '1'})

        self.run_command('ec2-credentials-create --tenant-id 1')
        self.fake_client.assert_called_anytime(
            'POST', '/users/1/credentials/OS-EC2',
            {'tenant_id': '1'})

        self.run_command('ec2-credentials-create')
        self.fake_client.assert_called_anytime(
            'POST', '/users/1/credentials/OS-EC2',
            {'tenant_id': '1'})

    def test_ec2_credentials_delete(self):
        self.run_command('ec2-credentials-delete --access 2 --user-id 1')
        self.fake_client.assert_called_anytime(
            'DELETE', '/users/1/credentials/OS-EC2/2')

        self.run_command('ec2-credentials-delete --access 2')
        self.fake_client.assert_called_anytime(
            'DELETE', '/users/1/credentials/OS-EC2/2')

    def test_ec2_credentials_list(self):
        self.run_command('ec2-credentials-list --user-id 1')
        self.fake_client.assert_called_anytime(
            'GET', '/users/1/credentials/OS-EC2')

        self.run_command('ec2-credentials-list')
        self.fake_client.assert_called_anytime(
            'GET', '/users/1/credentials/OS-EC2')

    def test_ec2_credentials_get(self):
        self.run_command('ec2-credentials-get --access 2 --user-id 1')
        self.fake_client.assert_called_anytime(
            'GET', '/users/1/credentials/OS-EC2/2')

    def test_bootstrap(self):
        self.run_command('bootstrap --user-name new-user'
                         ' --pass 1 --role-name admin'
                         ' --tenant-name new-tenant')
        self.fake_client.assert_called_anytime(
            'POST', '/users',
            {'user':
                {'email': None,
                 'password': '1',
                 'enabled': True,
                 'name': 'new-user',
                 'tenantId': None}})
        self.run_command('bootstrap --user-name new-user'
                         ' --pass 1 --role-name admin'
                         ' --tenant-name new-tenant')
        self.fake_client.assert_called_anytime(
            'POST', '/tenants',
            {"tenant": {"enabled": True,
                        "name": "new-tenant",
                        "description": None}})
        self.run_command('bootstrap --user-name new-user'
                         ' --pass 1 --role-name new-role'
                         ' --tenant-name new-tenant')
        self.fake_client.assert_called_anytime(
            'POST', '/OS-KSADM/roles',
            {"role": {"name": "new-role"}})

        self.run_command('bootstrap --user-name'
                         ' new-user --pass 1 --role-name admin'
                         ' --tenant-name new-tenant')
        self.fake_client.assert_called_anytime(
            'PUT', '/tenants/1/users/1/roles/OS-KSADM/1')

    def test_bash_completion(self):
        self.run_command('bash-completion')

    def test_help(self):
        out = self.run_command('help')
        required = 'usage: keystone'
        self.assertThat(out, matchers.MatchesRegex(required))

    def test_password_update(self):
        self.run_command('password-update --current-password oldpass'
                         ' --new-password newpass')
        self.fake_client.assert_called_anytime(
            'PATCH', '/OS-KSCRUD/users/1',
            {'user':
                {'original_password': 'oldpass',
                 'password': 'newpass'}})

    def test_endpoint_create(self):
        self.run_command('endpoint-create --service-id 1')
        self.fake_client.assert_called_anytime(
            'POST', '/endpoints',
            {'endpoint':
                {'adminurl': None,
                 'service_id': '1',
                 'region': 'regionOne',
                 'internalurl': None,
                 'publicurl': None}})

    def test_endpoint_list(self):
        self.run_command('endpoint-list')
        self.fake_client.assert_called_anytime('GET', '/endpoints')
