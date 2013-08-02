import json
import mock

import requests

from keystoneclient.v3 import client

from tests import utils
from tests.v3 import client_fixtures


class KeystoneClientTest(utils.TestCase):
    def setUp(self):
        super(KeystoneClientTest, self).setUp()

        domain_scoped_fake_resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(client_fixtures.DOMAIN_SCOPED_TOKEN),
            "headers": client_fixtures.AUTH_RESPONSE_HEADERS
        })
        self.domain_scoped_mock_req = mock.Mock(
            return_value=domain_scoped_fake_resp)

        project_scoped_fake_resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(client_fixtures.PROJECT_SCOPED_TOKEN),
            "headers": client_fixtures.AUTH_RESPONSE_HEADERS
        })
        self.project_scoped_mock_req = mock.Mock(
            return_value=project_scoped_fake_resp)

        unscoped_fake_resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(client_fixtures.UNSCOPED_TOKEN),
            "headers": client_fixtures.AUTH_RESPONSE_HEADERS
        })
        self.unscoped_mock_req = mock.Mock(return_value=unscoped_fake_resp)

        trust_fake_resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(client_fixtures.TRUST_TOKEN),
            "headers": client_fixtures.AUTH_RESPONSE_HEADERS
        })
        self.trust_mock_req = mock.Mock(return_value=trust_fake_resp)

    def test_unscoped_init(self):
        with mock.patch.object(requests, "request", self.unscoped_mock_req):
            c = client.Client(user_domain_name='exampledomain',
                              username='exampleuser',
                              password='password',
                              auth_url='http://somewhere/')
            self.assertIsNotNone(c.auth_ref)
            self.assertFalse(c.auth_ref.domain_scoped)
            self.assertFalse(c.auth_ref.project_scoped)
            self.assertEquals(c.auth_user_id,
                              'c4da488862bd435c9e6c0275a0d0e49a')

    def test_domain_scoped_init(self):
        with mock.patch.object(requests,
                               "request",
                               self.domain_scoped_mock_req):
            c = client.Client(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                              password='password',
                              domain_name='exampledomain',
                              auth_url='http://somewhere/')
            self.assertIsNotNone(c.auth_ref)
            self.assertTrue(c.auth_ref.domain_scoped)
            self.assertFalse(c.auth_ref.project_scoped)
            self.assertEquals(c.auth_user_id,
                              'c4da488862bd435c9e6c0275a0d0e49a')
            self.assertEquals(c.auth_domain_id,
                              '8e9283b7ba0b1038840c3842058b86ab')

    def test_project_scoped_init(self):
        with mock.patch.object(requests,
                               "request",
                               self.project_scoped_mock_req):
            c = client.Client(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                              password='password',
                              user_domain_name='exampledomain',
                              project_name='exampleproject',
                              auth_url='http://somewhere/')
            self.assertIsNotNone(c.auth_ref)
            self.assertFalse(c.auth_ref.domain_scoped)
            self.assertTrue(c.auth_ref.project_scoped)
            self.assertEquals(c.auth_user_id,
                              'c4da488862bd435c9e6c0275a0d0e49a')
            self.assertEquals(c.auth_tenant_id,
                              '225da22d3ce34b15877ea70b2a575f58')

    def test_auth_ref_load(self):
        with mock.patch.object(requests,
                               "request",
                               self.project_scoped_mock_req):
            c = client.Client(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                              password='password',
                              project_id='225da22d3ce34b15877ea70b2a575f58',
                              auth_url='http://somewhere/')
            cache = json.dumps(c.auth_ref)
            new_client = client.Client(auth_ref=json.loads(cache))
            self.assertIsNotNone(new_client.auth_ref)
            self.assertFalse(new_client.auth_ref.domain_scoped)
            self.assertTrue(new_client.auth_ref.project_scoped)
            self.assertEquals(new_client.username, 'exampleuser')
            self.assertIsNone(new_client.password)
            self.assertEqual(new_client.management_url,
                             'http://admin:35357/v3')

    def test_auth_ref_load_with_overridden_arguments(self):
        with mock.patch.object(requests,
                               "request",
                               self.project_scoped_mock_req):
            c = client.Client(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                              password='password',
                              project_id='225da22d3ce34b15877ea70b2a575f58',
                              auth_url='http://somewhere/')
            cache = json.dumps(c.auth_ref)
            new_auth_url = "http://new-public:5000/v3"
            new_client = client.Client(auth_ref=json.loads(cache),
                                       auth_url=new_auth_url)
            self.assertIsNotNone(new_client.auth_ref)
            self.assertFalse(new_client.auth_ref.domain_scoped)
            self.assertTrue(new_client.auth_ref.project_scoped)
            self.assertEquals(new_client.auth_url, new_auth_url)
            self.assertEquals(new_client.username, 'exampleuser')
            self.assertIsNone(new_client.password)
            self.assertEqual(new_client.management_url,
                             'http://admin:35357/v3')

    def test_trust_init(self):
        with mock.patch.object(requests, "request", self.trust_mock_req):
            c = client.Client(user_domain_name='exampledomain',
                              username='exampleuser',
                              password='password',
                              auth_url='http://somewhere/',
                              trust_id='fe0aef')
            self.assertIsNotNone(c.auth_ref)
            self.assertFalse(c.auth_ref.domain_scoped)
            self.assertFalse(c.auth_ref.project_scoped)
            self.assertEqual(c.auth_ref.trust_id, 'fe0aef')
            self.assertTrue(c.auth_ref.trust_scoped)
            self.assertEquals(c.auth_user_id, '0ca8f6')
