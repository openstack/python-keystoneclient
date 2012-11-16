import copy
import urlparse
import json

import requests

from keystoneclient.v2_0 import ec2
from tests import utils


class EC2Tests(utils.TestCase):
    def setUp(self):
        super(EC2Tests, self).setUp()
        self.TEST_REQUEST_HEADERS = {
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
        }
        self.TEST_POST_HEADERS = {
            'Content-Type': 'application/json',
            'X-Auth-Token': 'aToken',
            'User-Agent': 'python-keystoneclient',
        }

    def test_create(self):
        user_id = 'usr'
        tenant_id = 'tnt'
        req_body = {
            "tenant_id": tenant_id,
        }
        resp_body = {
            "credential": {
                "access": "access",
                "secret": "secret",
                "tenant_id": tenant_id,
                "created": "12/12/12",
                "enabled": True,
            }
        }
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        url = urlparse.urljoin(self.TEST_URL,
                               'v2.0/users/%s/credentials/OS-EC2' % user_id)
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_POST_HEADERS
        kwargs['data'] = json.dumps(req_body)
        requests.request('POST',
                         url,
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        cred = self.client.ec2.create(user_id, tenant_id)
        self.assertTrue(isinstance(cred, ec2.EC2))
        self.assertEqual(cred.tenant_id, tenant_id)
        self.assertEqual(cred.enabled, True)
        self.assertEqual(cred.access, 'access')
        self.assertEqual(cred.secret, 'secret')

    def test_get(self):
        user_id = 'usr'
        tenant_id = 'tnt'
        resp_body = {
            "credential": {
                "access": "access",
                "secret": "secret",
                "tenant_id": tenant_id,
                "created": "12/12/12",
                "enabled": True,
            }
        }
        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        url = urlparse.urljoin(self.TEST_URL,
                               'v2.0/users/%s/credentials/OS-EC2/%s' %
                               (user_id, 'access'))
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('GET',
                         url,
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        cred = self.client.ec2.get(user_id, 'access')
        self.assertTrue(isinstance(cred, ec2.EC2))
        self.assertEqual(cred.tenant_id, tenant_id)
        self.assertEqual(cred.enabled, True)
        self.assertEqual(cred.access, 'access')
        self.assertEqual(cred.secret, 'secret')

    def test_list(self):
        user_id = 'usr'
        tenant_id = 'tnt'
        resp_body = {
            "credentials": {
                "values": [
                    {
                        "access": "access",
                        "secret": "secret",
                        "tenant_id": tenant_id,
                        "created": "12/12/12",
                        "enabled": True,
                    },
                    {
                        "access": "another",
                        "secret": "key",
                        "tenant_id": tenant_id,
                        "created": "12/12/31",
                        "enabled": True,
                    }
                ]
            }
        }

        resp = utils.TestResponse({
            "status_code": 200,
            "text": json.dumps(resp_body),
        })

        url = urlparse.urljoin(self.TEST_URL,
                               'v2.0/users/%s/credentials/OS-EC2' % user_id)
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('GET',
                         url,
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        creds = self.client.ec2.list(user_id)
        self.assertTrue(len(creds), 2)
        cred = creds[0]
        self.assertTrue(isinstance(cred, ec2.EC2))
        self.assertEqual(cred.tenant_id, tenant_id)
        self.assertEqual(cred.enabled, True)
        self.assertEqual(cred.access, 'access')
        self.assertEqual(cred.secret, 'secret')

    def test_delete(self):
        user_id = 'usr'
        access = 'access'
        resp = utils.TestResponse({
            "status_code": 204,
            "text": "",
        })

        url = urlparse.urljoin(self.TEST_URL,
                               'v2.0/users/%s/credentials/OS-EC2/%s' %
                               (user_id, access))
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.TEST_REQUEST_HEADERS
        requests.request('DELETE',
                         url,
                         **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.client.ec2.delete(user_id, access)
