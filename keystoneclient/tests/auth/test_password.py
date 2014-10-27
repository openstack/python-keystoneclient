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

import uuid

from keystoneclient.auth.identity.generic import password
from keystoneclient.auth.identity import v2
from keystoneclient.auth.identity import v3
from keystoneclient.tests.auth import utils


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
