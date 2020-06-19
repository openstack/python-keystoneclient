# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
from unittest import mock
import uuid


from keystoneclient.auth.identity.generic import password
from keystoneclient.auth.identity import v2
from keystoneclient.auth.identity import v3
from keystoneclient.auth.identity.v3 import password as v3_password
from keystoneclient.tests.unit.auth import utils


class PasswordTests(utils.GenericPluginTestCase):

    PLUGIN_CLASS = password.Password
    V2_PLUGIN_CLASS = v2.Password
    V3_PLUGIN_CLASS = v3.Password

    def new_plugin(self, **kwargs):
        kwargs.setdefault('username', uuid.uuid4().hex)
        kwargs.setdefault('password', uuid.uuid4().hex)
        return super(PasswordTests, self).new_plugin(**kwargs)

    def test_with_user_domain_params(self):
        self.stub_discovery()

        self.assertCreateV3(domain_id=uuid.uuid4().hex,
                            user_domain_id=uuid.uuid4().hex)

    def test_v3_user_params_v2_url(self):
        self.stub_discovery(v3=False)
        self.assertDiscoveryFailure(user_domain_id=uuid.uuid4().hex)

    def test_options(self):
        opts = [o.name for o in self.PLUGIN_CLASS.get_options()]

        allowed_opts = ['username',
                        'user-domain-id',
                        'user-domain-name',
                        'user-id',
                        'password',

                        'domain-id',
                        'domain-name',
                        'tenant-id',
                        'tenant-name',
                        'project-id',
                        'project-name',
                        'project-domain-id',
                        'project-domain-name',
                        'trust-id',
                        'auth-url']

        self.assertEqual(set(allowed_opts), set(opts))
        self.assertEqual(len(allowed_opts), len(opts))

    def test_symbols(self):
        self.assertIs(v3.Password, v3_password.Password)
        self.assertIs(v3.PasswordMethod, v3_password.PasswordMethod)

    @mock.patch('sys.stdin', autospec=True)
    def test_prompt_password(self, mock_stdin):
        parser = argparse.ArgumentParser()
        self.PLUGIN_CLASS.register_argparse_arguments(parser)

        username = uuid.uuid4().hex
        user_domain_id = uuid.uuid4().hex
        auth_url = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        password = uuid.uuid4().hex

        opts = parser.parse_args(['--os-username', username,
                                  '--os-auth-url', auth_url,
                                  '--os-user-domain-id', user_domain_id,
                                  '--os-project-id', project_id])

        with mock.patch('getpass.getpass') as mock_getpass:
            mock_getpass.return_value = password
            mock_stdin.isatty = lambda: True

            plugin = self.PLUGIN_CLASS.load_from_argparse_arguments(opts)

            self.assertEqual(auth_url, plugin.auth_url)
            self.assertEqual(username, plugin._username)
            self.assertEqual(project_id, plugin._project_id)
            self.assertEqual(user_domain_id, plugin._user_domain_id)
            self.assertEqual(password, plugin._password)
