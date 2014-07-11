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
import uuid

from keystoneclient.auth import cli
from keystoneclient.tests.auth import utils


class CliTests(utils.TestCase):

    def setUp(self):
        super(CliTests, self).setUp()
        self.p = argparse.ArgumentParser()

    def test_creating_with_no_args(self):
        ret = cli.register_argparse_arguments(self.p, [])
        self.assertIsNone(ret)
        self.assertIn('--os-auth-plugin', self.p.format_usage())

    def test_load_with_nothing(self):
        cli.register_argparse_arguments(self.p, [])
        opts = self.p.parse_args([])
        self.assertIsNone(cli.load_from_argparse_arguments(opts))

    @utils.mock_plugin
    def test_basic_params_added(self, m):
        name = uuid.uuid4().hex
        argv = ['--os-auth-plugin', name]
        ret = cli.register_argparse_arguments(self.p, argv)
        self.assertIs(utils.MockPlugin, ret)

        for n in ('--os-a-int', '--os-a-bool', '--os-a-float'):
            self.assertIn(n, self.p.format_usage())

        m.assert_called_once_with(name)

    @utils.mock_plugin
    def test_param_loading(self, m):
        name = uuid.uuid4().hex
        argv = ['--os-auth-plugin', name,
                '--os-a-int', str(self.a_int),
                '--os-a-float', str(self.a_float),
                '--os-a-bool', str(self.a_bool)]

        klass = cli.register_argparse_arguments(self.p, argv)
        self.assertIs(utils.MockPlugin, klass)

        opts = self.p.parse_args(argv)
        self.assertEqual(name, opts.os_auth_plugin)

        a = cli.load_from_argparse_arguments(opts)
        self.assertTestVals(a)

    @utils.mock_plugin
    def test_default_options(self, m):
        name = uuid.uuid4().hex
        argv = ['--os-auth-plugin', name,
                '--os-a-float', str(self.a_float)]

        klass = cli.register_argparse_arguments(self.p, argv)
        self.assertIs(utils.MockPlugin, klass)

        opts = self.p.parse_args(argv)
        self.assertEqual(name, opts.os_auth_plugin)

        a = cli.load_from_argparse_arguments(opts)

        self.assertEqual(self.a_float, a['a_float'])
        self.assertEqual(3, a['a_int'])
