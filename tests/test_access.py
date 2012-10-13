from keystoneclient import access
from tests import utils

UNSCOPED_TOKEN = {
    u'access': {u'serviceCatalog': {},
                u'token': {u'expires': u'2012-10-03T16:58:01Z',
                           u'id': u'3e2813b7ba0b4006840c3825860b86ed'},
                u'user': {u'id': u'c4da488862bd435c9e6c0275a0d0e49a',
                          u'name': u'exampleuser',
                          u'roles': [],
                          u'roles_links': [],
                          u'username': u'exampleuser'}
                }
}

PROJECT_SCOPED_TOKEN = {
    u'access': {
        u'serviceCatalog': [{
            u'endpoints': [{
    u'adminURL': u'http://admin:8776/v1/225da22d3ce34b15877ea70b2a575f58',
    u'internalURL':
    u'http://internal:8776/v1/225da22d3ce34b15877ea70b2a575f58',
    u'publicURL':
    u'http://public.com:8776/v1/225da22d3ce34b15877ea70b2a575f58',
    u'region': u'RegionOne'
            }],
            u'endpoints_links': [],
            u'name': u'Volume Service',
            u'type': u'volume'},
            {u'endpoints': [{
    u'adminURL': u'http://admin:9292/v1',
    u'internalURL': u'http://internal:9292/v1',
    u'publicURL': u'http://public.com:9292/v1',
    u'region': u'RegionOne'}],
                u'endpoints_links': [],
                u'name': u'Image Service',
                u'type': u'image'},
            {u'endpoints': [{
u'adminURL': u'http://admin:8774/v2/225da22d3ce34b15877ea70b2a575f58',
u'internalURL': u'http://internal:8774/v2/225da22d3ce34b15877ea70b2a575f58',
u'publicURL': u'http://public.com:8774/v2/225da22d3ce34b15877ea70b2a575f58',
u'region': u'RegionOne'}],
                u'endpoints_links': [],
                u'name': u'Compute Service',
                u'type': u'compute'},
            {u'endpoints': [{
u'adminURL': u'http://admin:8773/services/Admin',
u'internalURL': u'http://internal:8773/services/Cloud',
u'publicURL': u'http://public.com:8773/services/Cloud',
u'region': u'RegionOne'}],
                u'endpoints_links': [],
                u'name': u'EC2 Service',
                u'type': u'ec2'},
            {u'endpoints': [{
u'adminURL': u'http://admin:35357/v2.0',
u'internalURL': u'http://internal:5000/v2.0',
u'publicURL': u'http://public.com:5000/v2.0',
u'region': u'RegionOne'}],
                u'endpoints_links': [],
                u'name': u'Identity Service',
                u'type': u'identity'}],
        u'token': {u'expires': u'2012-10-03T16:53:36Z',
                   u'id': u'04c7d5ffaeef485f9dc69c06db285bdb',
                   u'tenant': {u'description': u'',
                               u'enabled': True,
                               u'id': u'225da22d3ce34b15877ea70b2a575f58',
                               u'name': u'exampleproject'}},
        u'user': {u'id': u'c4da488862bd435c9e6c0275a0d0e49a',
                  u'name': u'exampleuser',
                  u'roles': [{u'id': u'edc12489faa74ee0aca0b8a0b4d74a74',
                              u'name': u'Member'}],
                  u'roles_links': [],
                  u'username': u'exampleuser'}
    }
}


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
