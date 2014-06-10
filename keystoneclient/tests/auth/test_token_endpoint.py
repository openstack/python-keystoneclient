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

import httpretty

from keystoneclient.auth import token_endpoint
from keystoneclient import session
from keystoneclient.tests import utils


class TokenEndpointTest(utils.TestCase):

    TEST_TOKEN = 'aToken'
    TEST_URL = 'http://server/prefix'

    @httpretty.activate
    def test_basic_case(self):
        httpretty.register_uri(httpretty.GET, self.TEST_URL, body='body')

        a = token_endpoint.Token(self.TEST_URL, self.TEST_TOKEN)
        s = session.Session(auth=a)

        data = s.get(self.TEST_URL, authenticated=True)

        self.assertEqual(data.text, 'body')
        self.assertRequestHeaderEqual('X-Auth-Token', self.TEST_TOKEN)

    @httpretty.activate
    def test_basic_endpoint_case(self):
        self.stub_url(httpretty.GET, ['p'], body='body')
        a = token_endpoint.Token(self.TEST_URL, self.TEST_TOKEN)
        s = session.Session(auth=a)

        data = s.get('/p',
                     authenticated=True,
                     endpoint_filter={'service': 'identity'})

        self.assertEqual(self.TEST_URL, a.get_endpoint(s))
        self.assertEqual('body', data.text)
        self.assertRequestHeaderEqual('X-Auth-Token', self.TEST_TOKEN)
