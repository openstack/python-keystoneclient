from keystoneclient import access
from tests import utils
from tests import client_fixtures

UNSCOPED_TOKEN = client_fixtures.UNSCOPED_TOKEN
PROJECT_SCOPED_TOKEN = client_fixtures.PROJECT_SCOPED_TOKEN


class AccessInfoTest(utils.TestCase):
    def test_building_unscoped_accessinfo(self):
        auth_ref = access.AccessInfo(UNSCOPED_TOKEN['access'])

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

    def test_building_scoped_accessinfo(self):
        auth_ref = access.AccessInfo(PROJECT_SCOPED_TOKEN['access'])

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

        self.assertTrue(auth_ref.scoped)
