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

from unittest import mock
import uuid

from oslo_config import cfg
from oslo_config import fixture as config

from keystoneclient.auth import base
from keystoneclient.auth import conf
from keystoneclient import exceptions
from keystoneclient.tests.unit.auth import utils


class ConfTests(utils.TestCase):

    def setUp(self):
        super(ConfTests, self).setUp()
        self.deprecations.expect_deprecations()
        self.conf_fixture = self.useFixture(config.Config())

        # NOTE(jamielennox): we register the basic config options first because
        # we need them in place before we can stub them. We will need to run
        # the register again after we stub the auth section and auth plugin so
        # it can load the plugin specific options.
        conf.register_conf_options(self.conf_fixture.conf, group=self.GROUP)

    def test_loading_v2(self):
        pass

    def test_loading_v3(self):
        pass

    def test_loading_invalid_plugin(self):
        auth_plugin = uuid.uuid4().hex
        self.conf_fixture.config(auth_plugin=auth_plugin,
                                 group=self.GROUP)

        e = self.assertRaises(exceptions.NoMatchingPlugin,
                              conf.load_from_conf_options,
                              self.conf_fixture.conf,
                              self.GROUP)

        self.assertEqual(auth_plugin, e.name)

    def test_loading_with_no_data(self):
        self.assertIsNone(conf.load_from_conf_options(self.conf_fixture.conf,
                                                      self.GROUP))

    @mock.patch('stevedore.DriverManager')
    def test_other_params(self, m):
        m.return_value = utils.MockManager(utils.MockPlugin)
        driver_name = uuid.uuid4().hex

        self.conf_fixture.register_opts(utils.MockPlugin.get_options(),
                                        group=self.GROUP)
        self.conf_fixture.config(auth_plugin=driver_name,
                                 group=self.GROUP,
                                 **self.TEST_VALS)

        a = conf.load_from_conf_options(self.conf_fixture.conf, self.GROUP)
        self.assertTestVals(a)

        m.assert_called_once_with(namespace=base.PLUGIN_NAMESPACE,
                                  name=driver_name,
                                  invoke_on_load=False)

    @utils.mock_plugin
    def test_same_section(self, m):
        self.conf_fixture.register_opts(utils.MockPlugin.get_options(),
                                        group=self.GROUP)
        conf.register_conf_options(self.conf_fixture.conf, group=self.GROUP)
        self.conf_fixture.config(auth_plugin=uuid.uuid4().hex,
                                 group=self.GROUP,
                                 **self.TEST_VALS)

        a = conf.load_from_conf_options(self.conf_fixture.conf, self.GROUP)
        self.assertTestVals(a)

    @utils.mock_plugin
    def test_diff_section(self, m):
        section = uuid.uuid4().hex

        self.conf_fixture.config(auth_section=section, group=self.GROUP)
        conf.register_conf_options(self.conf_fixture.conf, group=self.GROUP)

        self.conf_fixture.register_opts(utils.MockPlugin.get_options(),
                                        group=section)
        self.conf_fixture.config(group=section,
                                 auth_plugin=uuid.uuid4().hex,
                                 **self.TEST_VALS)

        a = conf.load_from_conf_options(self.conf_fixture.conf, self.GROUP)
        self.assertTestVals(a)

    def test_plugins_are_all_opts(self):
        pass

    def test_get_common(self):
        opts = conf.get_common_conf_options()
        for opt in opts:
            self.assertIsInstance(opt, cfg.Opt)
        self.assertEqual(2, len(opts))

    def test_get_named(self):
        pass
