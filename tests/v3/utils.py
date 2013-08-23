import copy
import json
import time
import urlparse
import uuid

import mock
from mox3 import mox
import requests
import testtools

from .. import utils

from keystoneclient.v3 import client

TestResponse = utils.TestResponse


def parameterize(ref):
    """Rewrites attributes to match the kwarg naming convention in client.

    >>> parameterize({'project_id': 0})
    {'project': 0}

    """
    params = ref.copy()
    for key in ref:
        if key[-3:] == '_id':
            params.setdefault(key[:-3], params.pop(key))
    return params


class TestClient(client.Client):

    def serialize(self, entity):
        return json.dumps(entity, sort_keys=True)


class TestCase(testtools.TestCase):
    TEST_DOMAIN_ID = '1'
    TEST_DOMAIN_NAME = 'aDomain'
    TEST_TENANT_ID = '1'
    TEST_TENANT_NAME = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'
    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v3')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v3')
    TEST_REQUEST_BASE = {
        'verify': True,
    }

    TEST_SERVICE_CATALOG = [{
        "endpoints": [{
            "url": "http://cdn.admin-nets.local:8774/v1.0/",
            "region": "RegionOne",
            "interface": "public"
        }, {
            "url": "http://127.0.0.1:8774/v1.0",
            "region": "RegionOne",
            "interface": "internal"
        }, {
            "url": "http://cdn.admin-nets.local:8774/v1.0",
            "region": "RegionOne",
            "interface": "admin"
        }],
        "type": "nova_compat"
    }, {
        "endpoints": [{
            "url": "http://nova/novapi/public",
            "region": "RegionOne",
            "interface": "public"
        }, {
            "url": "http://nova/novapi/internal",
            "region": "RegionOne",
            "interface": "internal"
        }, {
            "url": "http://nova/novapi/admin",
            "region": "RegionOne",
            "interface": "admin"
        }],
        "type": "compute"
    }, {
        "endpoints": [{
            "url": "http://glance/glanceapi/public",
            "region": "RegionOne",
            "interface": "public"
        }, {
            "url": "http://glance/glanceapi/internal",
            "region": "RegionOne",
            "interface": "internal"
        }, {
            "url": "http://glance/glanceapi/admin",
            "region": "RegionOne",
            "interface": "admin"
        }],
        "type": "image",
        "name": "glance"
    }, {
        "endpoints": [{
            "url": "http://127.0.0.1:5000/v3",
            "region": "RegionOne",
            "interface": "public"
        }, {
            "url": "http://127.0.0.1:5000/v3",
            "region": "RegionOne",
            "interface": "internal"
        }, {
            "url": "http://127.0.0.1:35357/v3",
            "region": "RegionOne",
            "interface": "admin"
        }],
        "type": "identity"
    }, {
        "endpoints": [{
            "url": "http://swift/swiftapi/public",
            "region": "RegionOne",
            "interface": "public"
        }, {
            "url": "http://swift/swiftapi/internal",
            "region": "RegionOne",
            "interface": "internal"
        }, {
            "url": "http://swift/swiftapi/admin",
            "region": "RegionOne",
            "interface": "admin"
        }],
        "type": "object-store"
    }]

    def setUp(self):
        super(TestCase, self).setUp()
        self.mox = mox.Mox()
        self.request_patcher = mock.patch.object(requests, 'request',
                                                 self.mox.CreateMockAnything())
        self.time_patcher = mock.patch.object(time, 'time',
                                              lambda: 1234)
        self.request_patcher.start()
        self.time_patcher.start()
        self.client = TestClient(username=self.TEST_USER,
                                 token=self.TEST_TOKEN,
                                 tenant_name=self.TEST_TENANT_NAME,
                                 auth_url=self.TEST_URL,
                                 endpoint=self.TEST_URL)

    def tearDown(self):
        self.request_patcher.stop()
        self.time_patcher.stop()
        self.mox.UnsetStubs()
        self.mox.VerifyAll()
        super(TestCase, self).tearDown()


class UnauthenticatedTestCase(testtools.TestCase):
    """Class used as base for unauthenticated calls."""
    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v3')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v3')
    TEST_REQUEST_BASE = {
        'verify': True,
    }

    def setUp(self):
        super(UnauthenticatedTestCase, self).setUp()
        self.mox = mox.Mox()

        self.request_patcher = mock.patch.object(requests, 'request',
                                                 self.mox.CreateMockAnything())
        self.time_patcher = mock.patch.object(time, 'time',
                                              lambda: 1234)
        self.request_patcher.start()

    def tearDown(self):
        self.request_patcher.stop()
        self.time_patcher.stop()
        self.mox.UnsetStubs()
        self.mox.VerifyAll()
        super(UnauthenticatedTestCase, self).tearDown()


class CrudTests(testtools.TestCase):
    key = None
    collection_key = None
    model = None
    manager = None
    path_prefix = None

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        return kwargs

    def additionalSetUp(self):
        self.headers = {
            'GET': {
                'X-Auth-Token': 'aToken',
                'User-Agent': 'python-keystoneclient',
            }
        }

        self.headers['HEAD'] = self.headers['GET'].copy()
        self.headers['DELETE'] = self.headers['GET'].copy()
        self.headers['PUT'] = self.headers['GET'].copy()
        self.headers['POST'] = self.headers['GET'].copy()
        self.headers['POST']['Content-Type'] = 'application/json'
        self.headers['PATCH'] = self.headers['POST'].copy()

    def serialize(self, entity):
        if isinstance(entity, dict):
            return json.dumps({self.key: entity}, sort_keys=True)
        if isinstance(entity, list):
            return json.dumps({self.collection_key: entity}, sort_keys=True)
        raise NotImplementedError('Are you sure you want to serialize that?')

    def _req_path(self):
        if self.path_prefix:
            return 'v3/%s/%s' % (self.path_prefix, self.collection_key)
        else:
            return 'v3/%s' % self.collection_key

    def test_create(self, ref=None, req_ref=None):
        ref = ref or self.new_ref()
        manager_ref = ref.copy()
        manager_ref.pop('id')

        # req_ref argument allows you to specify a different
        # signature for the request when the manager does some
        # conversion before doing the request (e.g converting
        # from datetime object to timestamp string)
        req_ref = req_ref or ref.copy()
        req_ref.pop('id')
        data = self.serialize(req_ref)
        resp = TestResponse({
            "status_code": 201,
            "text": data,
        })

        method = 'POST'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        kwargs['data'] = data

        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                self._req_path()),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned = self.manager.create(**parameterize(manager_ref))
        self.assertTrue(isinstance(returned, self.model))
        for attr in req_ref:
            self.assertEqual(
                getattr(returned, attr),
                req_ref[attr],
                'Expected different %s' % attr)

    def test_get(self, ref=None):
        ref = ref or self.new_ref()
        resp = TestResponse({
            "status_code": 200,
            "text": self.serialize(ref),
        })

        method = 'GET'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                '%s/%s' % (self._req_path(), ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned = self.manager.get(ref['id'])
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_list(self, ref_list=None, expected_path=None, **filter_kwargs):
        ref_list = ref_list or [self.new_ref(), self.new_ref()]
        resp = TestResponse({
            "status_code": 200,
            "text": self.serialize(ref_list),
        })

        method = 'GET'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                expected_path or self._req_path()),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned_list = self.manager.list(**filter_kwargs)
        self.assertTrue(len(returned_list))
        [self.assertTrue(isinstance(r, self.model)) for r in returned_list]

    def test_find(self, ref=None):
        ref = ref or self.new_ref()
        ref_list = [ref]
        resp = TestResponse({
            "status_code": 200,
            "text": self.serialize(ref_list),
        })

        method = 'GET'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        query = '?name=%s' % ref['name'] if hasattr(ref, 'name') else ''
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                '%s%s' % (self._req_path(), query)),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned = self.manager.find(name=getattr(ref, 'name', None))
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_update(self, ref=None):
        ref = ref or self.new_ref()
        req_ref = ref.copy()
        del req_ref['id']
        resp = TestResponse({
            "status_code": 200,
            "text": self.serialize(ref),
        })

        method = 'PATCH'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        kwargs['data'] = self.serialize(req_ref)
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                '%s/%s' % (self._req_path(), ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned = self.manager.update(ref['id'], **parameterize(req_ref))
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_delete(self, ref=None):
        ref = ref or self.new_ref()
        resp = TestResponse({
            "status_code": 204,
            "text": '',
        })

        method = 'DELETE'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                '%s/%s' % (self._req_path(), ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.delete(ref['id'])
