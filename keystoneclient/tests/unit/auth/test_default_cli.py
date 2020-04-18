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


from keystoneclient.auth.identity.generic import cli
from keystoneclient import exceptions
from keystoneclient.tests.unit import utils


class DefaultCliTests(utils.TestCase):

    def setUp(self):
        super(DefaultCliTests, self).setUp()
        self.deprecations.expect_deprecations()

    def new_plugin(self, argv):
        parser = argparse.ArgumentParser()
        cli.DefaultCLI.register_argparse_arguments(parser)
        opts = parser.parse_args(argv)
        return cli.DefaultCLI.load_from_argparse_arguments(opts)

    def test_endpoint_override(self):
        password = uuid.uuid4().hex
        url = uuid.uuid4().hex

        p = self.new_plugin(['--os-auth-url', 'url',
                             '--os-endpoint', url,
                             '--os-password', password])

        self.assertEqual(url, p.get_endpoint(None))
        self.assertEqual(password, p._password)

    def test_token_only_override(self):
        self.assertRaises(exceptions.CommandError,
                          self.new_plugin,
                          ['--os-token', uuid.uuid4().hex])

    def test_token_endpoint_override(self):
        token = uuid.uuid4().hex
        endpoint = uuid.uuid4().hex

        p = self.new_plugin(['--os-endpoint', endpoint,
                             '--os-token', token])

        self.assertEqual(endpoint, p.get_endpoint(None))
        self.assertEqual(token, p.get_token(None))

    def test_no_auth_url(self):
        exc = self.assertRaises(exceptions.CommandError,
                                self.new_plugin,
                                ['--os-username', uuid.uuid4().hex])

        self.assertIn('auth-url', str(exc))

    @mock.patch('sys.stdin', autospec=True)
    @mock.patch('getpass.getpass')
    def test_prompt_password(self, mock_getpass, mock_stdin):
        password = uuid.uuid4().hex

        mock_stdin.isatty = lambda: True
        mock_getpass.return_value = password

        p = self.new_plugin(['--os-auth-url', uuid.uuid4().hex,
                             '--os-username', uuid.uuid4().hex])

        self.assertEqual(password, p._password)

    @mock.patch('sys.stdin', autospec=True)
    @mock.patch('getpass.getpass')
    def test_prompt_no_password(self, mock_getpass, mock_stdin):
        mock_stdin.isatty = lambda: True
        mock_getpass.return_value = ''

        exc = self.assertRaises(exceptions.CommandError,
                                self.new_plugin,
                                ['--os-auth-url', uuid.uuid4().hex,
                                 '--os-username', uuid.uuid4().hex])

        self.assertIn('password', str(exc))
