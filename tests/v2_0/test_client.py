import json
import mock

import requests

from keystoneclient.v2_0 import client
from tests import utils
from tests.v2_0 import client_fixtures


class KeystoneClientTest(utils.TestCase):
    def setUp(self):
        super(KeystoneClientTest, self).setUp()

        scoped_fake_resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(client_fixtures.PROJECT_SCOPED_TOKEN)
        })
        self.scoped_mock_req = mock.Mock(return_value=scoped_fake_resp)

        unscoped_fake_resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(client_fixtures.UNSCOPED_TOKEN)
        })
        self.unscoped_mock_req = mock.Mock(return_value=unscoped_fake_resp)

    def test_unscoped_init(self):
        with mock.patch.object(requests, "request", self.unscoped_mock_req):
            c = client.Client(username='exampleuser',
                              password='password',
                              auth_url='http://somewhere/')
            self.assertIsNotNone(c.auth_ref)
            self.assertFalse(c.auth_ref.scoped)
            self.assertFalse(c.auth_ref.domain_scoped)
            self.assertFalse(c.auth_ref.project_scoped)
            self.assertIsNone(c.auth_ref.trust_id)
            self.assertFalse(c.auth_ref.trust_scoped)

    def test_scoped_init(self):
        with mock.patch.object(requests, "request", self.scoped_mock_req):
            c = client.Client(username='exampleuser',
                              password='password',
                              tenant_name='exampleproject',
                              auth_url='http://somewhere/')
            self.assertIsNotNone(c.auth_ref)
            self.assertTrue(c.auth_ref.scoped)
            self.assertTrue(c.auth_ref.project_scoped)
            self.assertFalse(c.auth_ref.domain_scoped)
            self.assertIsNone(c.auth_ref.trust_id)
            self.assertFalse(c.auth_ref.trust_scoped)

    def test_auth_ref_load(self):
        with mock.patch.object(requests, "request", self.scoped_mock_req):
            cl = client.Client(username='exampleuser',
                               password='password',
                               tenant_name='exampleproject',
                               auth_url='http://somewhere/')
            cache = json.dumps(cl.auth_ref)
            new_client = client.Client(auth_ref=json.loads(cache))
            self.assertIsNotNone(new_client.auth_ref)
            self.assertTrue(new_client.auth_ref.scoped)
            self.assertTrue(new_client.auth_ref.project_scoped)
            self.assertFalse(new_client.auth_ref.domain_scoped)
            self.assertIsNone(new_client.auth_ref.trust_id)
            self.assertFalse(new_client.auth_ref.trust_scoped)
            self.assertEquals(new_client.username, 'exampleuser')
            self.assertIsNone(new_client.password)
            self.assertEqual(new_client.management_url,
                             'http://admin:35357/v2.0')

    def test_auth_ref_load_with_overridden_arguments(self):
        with mock.patch.object(requests, "request", self.scoped_mock_req):
            cl = client.Client(username='exampleuser',
                               password='password',
                               tenant_name='exampleproject',
                               auth_url='http://somewhere/')
            cache = json.dumps(cl.auth_ref)
            new_auth_url = "http://new-public:5000/v2.0"
            new_client = client.Client(auth_ref=json.loads(cache),
                                       auth_url=new_auth_url)
            self.assertIsNotNone(new_client.auth_ref)
            self.assertTrue(new_client.auth_ref.scoped)
            self.assertTrue(new_client.auth_ref.scoped)
            self.assertTrue(new_client.auth_ref.project_scoped)
            self.assertFalse(new_client.auth_ref.domain_scoped)
            self.assertIsNone(new_client.auth_ref.trust_id)
            self.assertFalse(new_client.auth_ref.trust_scoped)
            self.assertEquals(new_client.auth_url, new_auth_url)
            self.assertEquals(new_client.username, 'exampleuser')
            self.assertIsNone(new_client.password)
            self.assertEqual(new_client.management_url,
                             'http://admin:35357/v2.0')
