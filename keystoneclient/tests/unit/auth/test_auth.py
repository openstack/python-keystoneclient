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

from keystoneclient import auth
from keystoneclient.auth import identity
from keystoneclient.tests.unit.auth import utils


class AuthTests(utils.TestCase):

    def test_plugin_names_in_available(self):
        with self.deprecations.expect_deprecations_here():
            plugins = auth.get_available_plugin_names()

        for p in ('password', 'v2password', 'v3password',
                  'token', 'v2token', 'v3token'):
            self.assertIn(p, plugins)

    def test_plugin_classes_in_available(self):
        with self.deprecations.expect_deprecations_here():
            plugins = auth.get_available_plugin_classes()

        self.assertIs(plugins['password'], identity.Password)
        self.assertIs(plugins['v2password'], identity.V2Password)
        self.assertIs(plugins['v3password'], identity.V3Password)

        self.assertIs(plugins['token'], identity.Token)
        self.assertIs(plugins['v2token'], identity.V2Token)
        self.assertIs(plugins['v3token'], identity.V3Token)
