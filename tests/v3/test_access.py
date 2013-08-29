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
from tests.v3 import client_fixtures
from tests.v3 import utils

TOKEN_RESPONSE = utils.TestResponse({
    "headers": client_fixtures.AUTH_RESPONSE_HEADERS
})
UNSCOPED_TOKEN = client_fixtures.UNSCOPED_TOKEN
DOMAIN_SCOPED_TOKEN = client_fixtures.DOMAIN_SCOPED_TOKEN
PROJECT_SCOPED_TOKEN = client_fixtures.PROJECT_SCOPED_TOKEN


class AccessInfoTest(utils.TestCase):
    def test_building_unscoped_accessinfo(self):
        auth_ref = access.AccessInfo.factory(resp=TOKEN_RESPONSE,
                                             body=UNSCOPED_TOKEN)

        self.assertTrue(auth_ref)
        self.assertIn('methods', auth_ref)
        self.assertIn('catalog', auth_ref)
        self.assertFalse(auth_ref['catalog'])

        self.assertEquals(auth_ref.auth_token,
                          '3e2813b7ba0b4006840c3825860b86ed')
        self.assertEquals(auth_ref.username, 'exampleuser')
        self.assertEquals(auth_ref.user_id, 'c4da488862bd435c9e6c0275a0d0e49a')

        self.assertEquals(auth_ref.project_name, None)
        self.assertEquals(auth_ref.project_id, None)

        self.assertEquals(auth_ref.auth_url, None)
        self.assertEquals(auth_ref.management_url, None)

        self.assertFalse(auth_ref.domain_scoped)
        self.assertFalse(auth_ref.project_scoped)

        self.assertEquals(auth_ref.user_domain_id,
                          '4e6893b7ba0b4006840c3845660b86ed')
        self.assertEquals(auth_ref.user_domain_name, 'exampledomain')

        self.assertIsNone(auth_ref.project_domain_id)
        self.assertIsNone(auth_ref.project_domain_name)

        self.assertEquals(auth_ref.expires, timeutils.parse_isotime(
                          UNSCOPED_TOKEN['token']['expires_at']))

    def test_will_expire_soon(self):
        expires = timeutils.utcnow() + datetime.timedelta(minutes=5)
        UNSCOPED_TOKEN['token']['expires_at'] = expires.isoformat()
        auth_ref = access.AccessInfo.factory(resp=TOKEN_RESPONSE,
                                             body=UNSCOPED_TOKEN)
        self.assertFalse(auth_ref.will_expire_soon(stale_duration=120))
        self.assertTrue(auth_ref.will_expire_soon(stale_duration=300))
        self.assertFalse(auth_ref.will_expire_soon())

    def test_building_domain_scoped_accessinfo(self):
        auth_ref = access.AccessInfo.factory(resp=TOKEN_RESPONSE,
                                             body=DOMAIN_SCOPED_TOKEN)

        self.assertTrue(auth_ref)
        self.assertIn('methods', auth_ref)
        self.assertIn('catalog', auth_ref)
        self.assertFalse(auth_ref['catalog'])

        self.assertEquals(auth_ref.auth_token,
                          '3e2813b7ba0b4006840c3825860b86ed')
        self.assertEquals(auth_ref.username, 'exampleuser')
        self.assertEquals(auth_ref.user_id, 'c4da488862bd435c9e6c0275a0d0e49a')

        self.assertEquals(auth_ref.domain_name, 'anotherdomain')
        self.assertEquals(auth_ref.domain_id,
                          '8e9283b7ba0b1038840c3842058b86ab')

        self.assertEquals(auth_ref.project_name, None)
        self.assertEquals(auth_ref.project_id, None)

        self.assertEquals(auth_ref.user_domain_id,
                          '4e6893b7ba0b4006840c3845660b86ed')
        self.assertEquals(auth_ref.user_domain_name, 'exampledomain')

        self.assertIsNone(auth_ref.project_domain_id)
        self.assertIsNone(auth_ref.project_domain_name)

        self.assertTrue(auth_ref.domain_scoped)
        self.assertFalse(auth_ref.project_scoped)

    def test_building_project_scoped_accessinfo(self):
        auth_ref = access.AccessInfo.factory(resp=TOKEN_RESPONSE,
                                             body=PROJECT_SCOPED_TOKEN)

        self.assertTrue(auth_ref)
        self.assertIn('methods', auth_ref)
        self.assertIn('catalog', auth_ref)
        self.assertTrue(auth_ref['catalog'])

        self.assertEquals(auth_ref.auth_token,
                          '3e2813b7ba0b4006840c3825860b86ed')
        self.assertEquals(auth_ref.username, 'exampleuser')
        self.assertEquals(auth_ref.user_id, 'c4da488862bd435c9e6c0275a0d0e49a')

        self.assertEquals(auth_ref.domain_name, None)
        self.assertEquals(auth_ref.domain_id, None)

        self.assertEquals(auth_ref.project_name, 'exampleproject')
        self.assertEquals(auth_ref.project_id,
                          '225da22d3ce34b15877ea70b2a575f58')

        self.assertEquals(auth_ref.tenant_name, auth_ref.project_name)
        self.assertEquals(auth_ref.tenant_id, auth_ref.project_id)

        self.assertEquals(auth_ref.auth_url,
                          ('http://public.com:5000/v3',))
        self.assertEquals(auth_ref.management_url,
                          ('http://admin:35357/v3',))

        self.assertEquals(auth_ref.project_domain_id,
                          '4e6893b7ba0b4006840c3845660b86ed')
        self.assertEquals(auth_ref.project_domain_name, 'exampledomain')

        self.assertEquals(auth_ref.user_domain_id,
                          '4e6893b7ba0b4006840c3845660b86ed')
        self.assertEquals(auth_ref.user_domain_name, 'exampledomain')

        self.assertFalse(auth_ref.domain_scoped)
        self.assertTrue(auth_ref.project_scoped)
