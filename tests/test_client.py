import copy
import json
import mock

import requests

from keystoneclient.v2_0 import client
from tests import client_fixtures
from tests import utils


fake_response = utils.TestResponse({
    "status_code": 200,
    "text": json.dumps(client_fixtures.PROJECT_SCOPED_TOKEN)
})
mock_request = mock.Mock(return_value=(fake_response))


class KeystoneclientTest(utils.TestCase):

    def test_scoped_init(self):
        with mock.patch.object(requests, "request", mock_request):
            cl = client.Client(username='exampleuser',
                               password='password',
                               auth_url='http://somewhere/')
            self.assertIsNotNone(cl.auth_ref)
            self.assertTrue(cl.auth_ref.scoped)

    def test_auth_ref_load(self):
        with mock.patch.object(requests, "request", mock_request):
            cl = client.Client(username='exampleuser',
                               password='password',
                               auth_url='http://somewhere/')
            cache = json.dumps(cl.auth_ref)
            new_client = client.Client(auth_ref=json.loads(cache))
            self.assertIsNotNone(new_client.auth_ref)
            self.assertTrue(new_client.auth_ref.scoped)
            self.assertEquals(new_client.username, 'exampleuser')
            self.assertIsNone(new_client.password)
            self.assertEqual(new_client.management_url,
                             'http://admin:35357/v2.0')
