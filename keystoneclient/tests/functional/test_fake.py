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

from keystoneclient.tests.functional import base


class FakeTests(base.TestCase):

    # NOTE(jamielennox): These are purely to have something that passes to
    # submit to the gate. After that is working this file can be removed and
    # the real tests can begin to be ported from tempest.

    def test_version(self):
        # NOTE(jamilennox): lol, 1st bug: version goes to stderr - can't test
        # value, however it tests that return value = 0 automatically.
        self.keystone('', flags='--version')
