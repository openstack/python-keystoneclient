import time

import httplib2
import mox
import unittest2 as unittest

from keystoneclient.v2_0 import client


class TestCase(unittest.TestCase):
    TEST_TENANT_ID = '1'
    TEST_TENANT_NAME = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'
    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v2.0')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v2.0')

    TEST_SERVICE_CATALOG = [{
        "endpoints": [{
            "adminURL": "http://cdn.admin-nets.local:8774/v1.0",
            "region": "RegionOne",
            "internalURL": "http://127.0.0.1:8774/v1.0",
            "publicURL": "http://cdn.admin-nets.local:8774/v1.0/"
        }],
        "type": "nova_compat",
        "name": "nova_compat"
    }, {
        "endpoints": [{
            "adminURL": "http://nova/novapi/admin",
            "region": "RegionOne",
            "internalURL": "http://nova/novapi/internal",
            "publicURL": "http://nova/novapi/public"
        }],
        "type": "compute",
        "name": "nova"
    }, {
        "endpoints": [{
            "adminURL": "http://glance/glanceapi/admin",
            "region": "RegionOne",
            "internalURL": "http://glance/glanceapi/internal",
            "publicURL": "http://glance/glanceapi/public"
        }],
        "type": "image",
        "name": "glance"
    }, {
        "endpoints": [{
            "adminURL": "http://127.0.0.1:35357/v2.0",
            "region": "RegionOne",
            "internalURL": "http://127.0.0.1:5000/v2.0",
            "publicURL": "http://127.0.0.1:5000/v2.0"
        }],
        "type": "identity",
        "name": "keystone"
    }, {
        "endpoints": [{
            "adminURL": "http://swift/swiftapi/admin",
            "region": "RegionOne",
            "internalURL": "http://swift/swiftapi/internal",
            "publicURL": "http://swift/swiftapi/public"
        }],
        "type": "object-store",
        "name": "swift"
    }]

    def setUp(self):
        super(TestCase, self).setUp()
        self.mox = mox.Mox()
        self._original_time = time.time
        time.time = lambda: 1234
        httplib2.Http.request = self.mox.CreateMockAnything()
        self.client = client.Client(username=self.TEST_USER,
                                    token=self.TEST_TOKEN,
                                    tenant_name=self.TEST_TENANT_NAME,
                                    auth_url=self.TEST_URL,
                                    endpoint=self.TEST_URL)

    def tearDown(self):
        time.time = self._original_time
        super(TestCase, self).tearDown()
        self.mox.UnsetStubs()
        self.mox.VerifyAll()


class UnauthenticatedTestCase(unittest.TestCase):
    """ Class used as base for unauthenticated calls """
    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v2.0')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v2.0')

    def setUp(self):
        super(UnauthenticatedTestCase, self).setUp()
        self.mox = mox.Mox()
        self._original_time = time.time
        time.time = lambda: 1234
        httplib2.Http.request = self.mox.CreateMockAnything()

    def tearDown(self):
        time.time = self._original_time
        super(UnauthenticatedTestCase, self).tearDown()
        self.mox.UnsetStubs()
        self.mox.VerifyAll()
