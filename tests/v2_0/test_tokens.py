# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import httpretty

from tests.v2_0 import utils


class TokenTests(utils.TestCase):
    @httpretty.activate
    def test_delete(self):
        self.stub_url(httpretty.DELETE, ['tokens', '1'], status=204)
        self.client.tokens.delete(1)
