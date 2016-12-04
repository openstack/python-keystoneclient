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

import os

import testtools

from keystoneclient.auth.identity import v2
from keystoneclient import session
from tempest.lib import base


class TestV2AccessInfo(base.BaseTestCase):

    def setUp(self):
        super(TestV2AccessInfo, self).setUp()

        self.session = session.Session()

    @testtools.skip("likely race condition, being skipped")
    def test_access_audit_id(self):
        unscoped_plugin = v2.Password(auth_url=os.environ.get('OS_AUTH_URL'),
                                      username=os.environ.get('OS_USERNAME'),
                                      password=os.environ.get('OS_PASSWORD'))

        unscoped_auth_ref = unscoped_plugin.get_access(self.session)

        self.assertIsNotNone(unscoped_auth_ref.audit_id)
        self.assertIsNone(unscoped_auth_ref.audit_chain_id)

        scoped_plugin = v2.Token(auth_url=os.environ.get('OS_AUTH_URL'),
                                 token=unscoped_auth_ref.auth_token,
                                 tenant_name=os.environ.get('OS_TENANT_NAME'))

        scoped_auth_ref = scoped_plugin.get_access(self.session)

        self.assertIsNotNone(scoped_auth_ref.audit_id)
        self.assertIsNotNone(scoped_auth_ref.audit_chain_id)

        self.assertEqual(unscoped_auth_ref.audit_id,
                         scoped_auth_ref.audit_chain_id)
