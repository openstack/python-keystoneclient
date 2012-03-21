import urlparse
import json

import httplib2

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
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
            })

        url = urlparse.urljoin(self.TEST_URL,
                               'v2.0/users/%s/credentials/OS-EC2' % user_id)
        httplib2.Http.request(url,
                              'POST',
                              body=json.dumps(req_body),
                              headers=self.TEST_POST_HEADERS) \
                              .AndReturn((resp, resp['body']))
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
        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
            })

        url = urlparse.urljoin(self.TEST_URL,
                               'v2.0/users/%s/credentials/OS-EC2/%s' %
                               (user_id, 'access'))
        httplib2.Http.request(url,
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
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

        resp = httplib2.Response({
            "status": 200,
            "body": json.dumps(resp_body),
            })

        url = urlparse.urljoin(self.TEST_URL,
                               'v2.0/users/%s/credentials/OS-EC2' % user_id)
        httplib2.Http.request(url,
                              'GET',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
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
        resp = httplib2.Response({
            "status": 200,
            "body": "",
            })

        url = urlparse.urljoin(self.TEST_URL,
                               'v2.0/users/%s/credentials/OS-EC2/%s' %
                               (user_id, access))
        httplib2.Http.request(url,
                              'DELETE',
                              headers=self.TEST_REQUEST_HEADERS) \
                              .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.client.ec2.delete(user_id, access)
