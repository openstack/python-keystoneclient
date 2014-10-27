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

from keystoneclient.auth.identity.generic import token
from keystoneclient.auth.identity import v2
from keystoneclient.auth.identity import v3
from keystoneclient.tests.auth import utils


class TokenTests(utils.GenericPluginTestCase):

    PLUGIN_CLASS = token.Token
    V2_PLUGIN_CLASS = v2.Token
    V3_PLUGIN_CLASS = v3.Token

    def new_plugin(self, **kwargs):
        kwargs.setdefault('token', uuid.uuid4().hex)
        return super(TokenTests, self).new_plugin(**kwargs)
