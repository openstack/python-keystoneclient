# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from keystoneclient import access
from keystoneclient.tests import client_fixtures
from keystoneclient.tests.v3 import utils


class TokenTests(utils.TestCase):

    def test_revoke_token_with_token_id(self):
        token_id = uuid.uuid4().hex
        self.stub_url('DELETE', ['/auth/tokens'], status_code=204)
        self.client.tokens.revoke_token(token_id)
        self.assertRequestHeaderEqual('X-Subject-Token', token_id)

    def test_revoke_token_with_access_info_instance(self):
        token_id = uuid.uuid4().hex
        examples = self.useFixture(client_fixtures.Examples())
        token_ref = examples.TOKEN_RESPONSES[examples.v3_UUID_TOKEN_DEFAULT]
        token = access.AccessInfoV3(token_id, token_ref['token'])
        self.stub_url('DELETE', ['/auth/tokens'], status_code=204)
        self.client.tokens.revoke_token(token)
        self.assertRequestHeaderEqual('X-Subject-Token', token_id)
