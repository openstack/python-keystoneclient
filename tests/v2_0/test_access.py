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

import datetime

from keystoneclient import access
from keystoneclient.openstack.common import timeutils
from tests import client_fixtures as token_data
from tests.v2_0 import client_fixtures
from tests.v2_0 import utils

UNSCOPED_TOKEN = client_fixtures.UNSCOPED_TOKEN
PROJECT_SCOPED_TOKEN = client_fixtures.PROJECT_SCOPED_TOKEN
DIABLO_TOKEN = token_data.TOKEN_RESPONSES[token_data.VALID_DIABLO_TOKEN]
GRIZZLY_TOKEN = token_data.TOKEN_RESPONSES[token_data.SIGNED_TOKEN_SCOPED_KEY]


class AccessInfoTest(utils.TestCase):
    def test_building_unscoped_accessinfo(self):
        auth_ref = access.AccessInfo.factory(body=UNSCOPED_TOKEN)

        self.assertTrue(auth_ref)
        self.assertIn('token', auth_ref)
        self.assertIn('serviceCatalog', auth_ref)
        self.assertFalse(auth_ref['serviceCatalog'])

        self.assertEquals(auth_ref.auth_token,
                          '3e2813b7ba0b4006840c3825860b86ed')
        self.assertEquals(auth_ref.username, 'exampleuser')
        self.assertEquals(auth_ref.user_id, 'c4da488862bd435c9e6c0275a0d0e49a')

        self.assertEquals(auth_ref.tenant_name, None)
        self.assertEquals(auth_ref.tenant_id, None)

        self.assertEquals(auth_ref.auth_url, None)
        self.assertEquals(auth_ref.management_url, None)

        self.assertFalse(auth_ref.scoped)
        self.assertFalse(auth_ref.domain_scoped)
        self.assertFalse(auth_ref.project_scoped)
        self.assertFalse(auth_ref.trust_scoped)

        self.assertIsNone(auth_ref.project_domain_id)
        self.assertIsNone(auth_ref.project_domain_name)
        self.assertEqual(auth_ref.user_domain_id, 'default')
        self.assertEqual(auth_ref.user_domain_name, 'Default')

        self.assertEquals(auth_ref.expires, timeutils.parse_isotime(
                          UNSCOPED_TOKEN['access']['token']['expires']))

    def test_will_expire_soon(self):
        expires = timeutils.utcnow() + datetime.timedelta(minutes=5)
        UNSCOPED_TOKEN['access']['token']['expires'] = expires.isoformat()
        auth_ref = access.AccessInfo.factory(body=UNSCOPED_TOKEN)
        self.assertFalse(auth_ref.will_expire_soon(stale_duration=120))
        self.assertTrue(auth_ref.will_expire_soon(stale_duration=300))
        self.assertFalse(auth_ref.will_expire_soon())

    def test_building_scoped_accessinfo(self):
        auth_ref = access.AccessInfo.factory(body=PROJECT_SCOPED_TOKEN)

        self.assertTrue(auth_ref)
        self.assertIn('token', auth_ref)
        self.assertIn('serviceCatalog', auth_ref)
        self.assertTrue(auth_ref['serviceCatalog'])

        self.assertEquals(auth_ref.auth_token,
                          '04c7d5ffaeef485f9dc69c06db285bdb')
        self.assertEquals(auth_ref.username, 'exampleuser')
        self.assertEquals(auth_ref.user_id, 'c4da488862bd435c9e6c0275a0d0e49a')

        self.assertEquals(auth_ref.tenant_name, 'exampleproject')
        self.assertEquals(auth_ref.tenant_id,
                          '225da22d3ce34b15877ea70b2a575f58')

        self.assertEquals(auth_ref.tenant_name, auth_ref.project_name)
        self.assertEquals(auth_ref.tenant_id, auth_ref.project_id)

        self.assertEquals(auth_ref.auth_url,
                          ('http://public.com:5000/v2.0',))
        self.assertEquals(auth_ref.management_url,
                          ('http://admin:35357/v2.0',))

        self.assertEqual(auth_ref.project_domain_id, 'default')
        self.assertEqual(auth_ref.project_domain_name, 'Default')
        self.assertEqual(auth_ref.user_domain_id, 'default')
        self.assertEqual(auth_ref.user_domain_name, 'Default')

        self.assertTrue(auth_ref.scoped)
        self.assertTrue(auth_ref.project_scoped)
        self.assertFalse(auth_ref.domain_scoped)

    def test_diablo_token(self):
        auth_ref = access.AccessInfo.factory(body=DIABLO_TOKEN)

        self.assertTrue(auth_ref)
        self.assertEquals(auth_ref.username, 'user_name1')
        self.assertEquals(auth_ref.project_id, 'tenant_id1')
        self.assertEquals(auth_ref.project_name, 'tenant_id1')
        self.assertEquals(auth_ref.project_domain_id, 'default')
        self.assertEquals(auth_ref.project_domain_name, 'Default')
        self.assertEquals(auth_ref.user_domain_id, 'default')
        self.assertEquals(auth_ref.user_domain_name, 'Default')
        self.assertFalse(auth_ref.scoped)

    def test_grizzly_token(self):
        auth_ref = access.AccessInfo.factory(body=GRIZZLY_TOKEN)

        self.assertEquals(auth_ref.project_id, 'tenant_id1')
        self.assertEquals(auth_ref.project_name, 'tenant_name1')
        self.assertEquals(auth_ref.project_domain_id, 'default')
        self.assertEquals(auth_ref.project_domain_name, 'Default')
        self.assertEquals(auth_ref.user_domain_id, 'default')
        self.assertEquals(auth_ref.user_domain_name, 'Default')
