import urlparse

import httplib2

from tests import utils


class TokenTests(utils.TestCase):
    def setUp(self):
        super(TokenTests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
                'X-Auth-Token': 'aToken',
                'User-Agent': 'python-keystoneclient'}
        self.TEST_POST_HEADERS = {
                'Content-Type': 'application/json',
                'X-Auth-Token': 'aToken',
                'User-Agent': 'python-keystoneclient'}

    def test_delete(self):
        resp = httplib2.Response({
            "status": 200,
            "body": ""})

        req = httplib2.Http.request(
                urlparse.urljoin(self.TEST_URL, 'v2.0/tokens/1'),
                'DELETE',
                headers=self.TEST_REQUEST_HEADERS)
        req.AndReturn((resp, resp['body']))

        self.mox.ReplayAll()

        self.client.tokens.delete(1)
