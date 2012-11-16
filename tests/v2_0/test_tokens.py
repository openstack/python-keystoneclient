import copy
import urlparse

import requests

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
        resp = utils.TestResponse({
            "status_code": 204,
            "text": ""})

        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request(
            'DELETE',
            urlparse.urljoin(self.TEST_URL, 'v2.0/tokens/1'),
            **kwargs).AndReturn((resp))

        self.mox.ReplayAll()

        self.client.tokens.delete(1)
