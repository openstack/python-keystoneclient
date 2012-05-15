import os
import mock
import httplib2

from keystoneclient import shell as openstack_shell
from keystoneclient.v2_0 import shell as shell_v2_0
from keystoneclient import exceptions
from tests import utils


DEFAULT_USERNAME = 'username'
DEFAULT_PASSWORD = 'password'
DEFAULT_TENANT_ID = 'tenant_id'
DEFAULT_TENANT_NAME = 'tenant_name'
DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/v2.0/'


class ShellTest(utils.TestCase):

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        global _old_env
        fake_env = {
            'OS_USERNAME': DEFAULT_USERNAME,
            'OS_PASSWORD': DEFAULT_PASSWORD,
            'OS_TENANT_ID': DEFAULT_TENANT_ID,
            'OS_TENANT_NAME': DEFAULT_TENANT_NAME,
            'OS_AUTH_URL': DEFAULT_AUTH_URL,
        }
        _old_env, os.environ = os.environ, fake_env.copy()

        # Make a fake shell object, a helping wrapper to call it, and a quick
        # way of asserting that certain API calls were made.
        global shell, _shell, assert_called, assert_called_anytime
        _shell = openstack_shell.OpenStackIdentityShell()
        shell = lambda cmd: _shell.main(cmd.split())

    def tearDown(self):
        global _old_env
        os.environ = _old_env

    def test_help_unknown_command(self):
        self.assertRaises(exceptions.CommandError, shell, 'help foofoo')

    def test_debug(self):
        httplib2.debuglevel = 0
        shell('--debug help')
        assert httplib2.debuglevel == 1

    def test_shell_args(self):
        do_tenant_mock = mock.MagicMock()
        with mock.patch('keystoneclient.v2_0.shell.do_user_list',
                        do_tenant_mock):
            shell('user-list')
            assert do_tenant_mock.called
            ((a, b), c) = do_tenant_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            shell('--os_auth_url http://0.0.0.0:5000/ --os_password xyzpdq '
                  '--os_tenant_id 1234 --os_tenant_name fred '
                  '--os_username barney '
                  '--os_identity_api_version 2.0 user-list')
            assert do_tenant_mock.called
            ((a, b), c) = do_tenant_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = ('http://0.0.0.0:5000/', 'xyzpdq', '1234',
                      'fred', 'barney', '2.0')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

    def test_shell_user_create_args(self):
        """Test user-create args"""
        do_uc_mock = mock.MagicMock()
        # grab the decorators for do_user_create
        uc_func = getattr(shell_v2_0, 'do_user_create')
        do_uc_mock.arguments = getattr(uc_func, 'arguments', [])
        with mock.patch('keystoneclient.v2_0.shell.do_user_create',
                        do_uc_mock):

            # Test case with one --tenant_id args present: ec2 creds
            shell('user-create --name=FOO '
                  '--pass=secrete --tenant_id=barrr --enabled=true')
            assert do_uc_mock.called
            ((a, b), c) = do_uc_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.name, b.passwd, b.enabled)
            expect = ('barrr', 'FOO', 'secrete', 'true')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # Test case with --os_tenant_id and --tenant_id args present
            shell('--os_tenant_id=os-tenant user-create --name=FOO '
                  '--pass=secrete --tenant_id=barrr --enabled=true')
            assert do_uc_mock.called
            ((a, b), c) = do_uc_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, 'os-tenant',
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.name, b.passwd, b.enabled)
            expect = ('barrr', 'FOO', 'secrete', 'true')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

    def test_do_tenant_create(self):
        do_tenant_mock = mock.MagicMock()
        with mock.patch('keystoneclient.v2_0.shell.do_tenant_create',
                        do_tenant_mock):
            shell('tenant-create')
            assert do_tenant_mock.called
            # FIXME(dtroyer): how do you test the decorators?
            #shell('tenant-create --tenant-name wilma '
            #        '--description "fred\'s wife"')
            #assert do_tenant_mock.called

    def test_do_tenant_list(self):
        do_tenant_mock = mock.MagicMock()
        with mock.patch('keystoneclient.v2_0.shell.do_tenant_list',
                        do_tenant_mock):
            shell('tenant-list')
            assert do_tenant_mock.called

    def test_shell_tenant_id_args(self):
        """Test a corner case where --tenant_id appears on the
           command-line twice"""
        do_ec2_mock = mock.MagicMock()
        # grab the decorators for do_ec2_create_credentials
        ec2_func = getattr(shell_v2_0, 'do_ec2_credentials_create')
        do_ec2_mock.arguments = getattr(ec2_func, 'arguments', [])
        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_create',
                        do_ec2_mock):

            # Test case with one --tenant_id args present: ec2 creds
            shell('ec2-credentials-create '
                  '--tenant_id=ec2-tenant --user_id=ec2-user')
            assert do_ec2_mock.called
            ((a, b), c) = do_ec2_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.user_id)
            expect = ('ec2-tenant', 'ec2-user')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

            # Test case with two --tenant_id args present
            shell('--os_tenant_id=os-tenant ec2-credentials-create '
                  '--tenant_id=ec2-tenant --user_id=ec2-user')
            assert do_ec2_mock.called
            ((a, b), c) = do_ec2_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, 'os-tenant',
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.tenant_id, b.user_id)
            expect = ('ec2-tenant', 'ec2-user')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))

    def test_do_ec2_get(self):
        do_shell_mock = mock.MagicMock()

        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_create',
                        do_shell_mock):
            shell('ec2-credentials-create')
            assert do_shell_mock.called

        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_get',
                        do_shell_mock):
            shell('ec2-credentials-get')
            assert do_shell_mock.called

        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_list',
                        do_shell_mock):
            shell('ec2-credentials-list')
            assert do_shell_mock.called

        with mock.patch('keystoneclient.v2_0.shell.do_ec2_credentials_delete',
                        do_shell_mock):
            shell('ec2-credentials-delete')
            assert do_shell_mock.called

    def test_do_endpoints(self):
        do_shell_mock = mock.MagicMock()
        # grab the decorators for do_endpoint_create
        shell_func = getattr(shell_v2_0, 'do_endpoint_create')
        do_shell_mock.arguments = getattr(shell_func, 'arguments', [])
        with mock.patch('keystoneclient.v2_0.shell.do_endpoint_create',
                        do_shell_mock):

            # Test create args
            shell('endpoint-create '
                  '--service_id=2 --publicurl=http://example.com:1234/go '
                  '--adminurl=http://example.com:9876/adm')
            assert do_shell_mock.called
            ((a, b), c) = do_shell_mock.call_args
            actual = (b.os_auth_url, b.os_password, b.os_tenant_id,
                      b.os_tenant_name, b.os_username,
                      b.os_identity_api_version)
            expect = (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                      DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
            actual = (b.service_id, b.publicurl, b.adminurl)
            expect = ('2',
                      'http://example.com:1234/go',
                      'http://example.com:9876/adm')
            self.assertTrue(all([x == y for x, y in zip(actual, expect)]))
