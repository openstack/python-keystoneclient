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
            assert (b.auth_url, b.password, b.os_tenant_id,
                    b.tenant_name, b.username, b.identity_api_version) == \
                   (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                    DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            shell('--auth_url http://0.0.0.0:5000/ --password xyzpdq '
                  '--tenant_id 1234 --tenant_name fred --username barney '
                  '--identity_api_version 2.0 user-list')
            assert do_tenant_mock.called
            ((a, b), c) = do_tenant_mock.call_args
            assert (b.auth_url, b.password, b.os_tenant_id,
                    b.tenant_name, b.username, b.identity_api_version) == \
                   ('http://0.0.0.0:5000/', 'xyzpdq', '1234',
                    'fred', 'barney', '2.0')

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
            # restore os_tenant_id when review 4295 is merged
            assert (b.auth_url, b.password,  # b.os_tenant_id,
                    b.tenant_name, b.username, b.identity_api_version) == \
                   (DEFAULT_AUTH_URL, DEFAULT_PASSWORD,  # DEFAULT_TENANT_ID,
                    DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            assert (b.tenant_id, b.name, b.passwd, b.enabled) == \
                   ('barrr', 'FOO', 'secrete', 'true')

            # Test case with two --tenant_id args present
            shell('--tenant_id=os-tenant user-create --name=FOO '
                  '--pass=secrete --tenant_id=barrr --enabled=true')
            assert do_uc_mock.called
            ((a, b), c) = do_uc_mock.call_args
            # restore os_tenant_id when review 4295 is merged
            assert (b.auth_url, b.password,  # b.os_tenant_id,
                    b.tenant_name, b.username, b.identity_api_version) == \
                   (DEFAULT_AUTH_URL, DEFAULT_PASSWORD,  # 'os-tenant',
                    DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            assert (b.tenant_id, b.name, b.passwd, b.enabled) == \
                   ('barrr', 'FOO', 'secrete', 'true')

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
                  '--tenant_id=ec2-tenant --user=ec2-user')
            assert do_ec2_mock.called
            ((a, b), c) = do_ec2_mock.call_args
            assert (b.auth_url, b.password, b.os_tenant_id,
                    b.tenant_name, b.username, b.identity_api_version) == \
                   (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, DEFAULT_TENANT_ID,
                    DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            assert (b.tenant_id, b.user) == ('ec2-tenant', 'ec2-user')

            # Test case with two --tenant_id args present
            shell('--tenant_id=os-tenant ec2-credentials-create '
                  '--tenant_id=ec2-tenant --user=ec2-user')
            assert do_ec2_mock.called
            ((a, b), c) = do_ec2_mock.call_args
            assert (b.auth_url, b.password, b.os_tenant_id,
                    b.tenant_name, b.username, b.identity_api_version) == \
                   (DEFAULT_AUTH_URL, DEFAULT_PASSWORD, 'os-tenant',
                    DEFAULT_TENANT_NAME, DEFAULT_USERNAME, '')
            assert (b.tenant_id, b.user) == ('ec2-tenant', 'ec2-user')

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
