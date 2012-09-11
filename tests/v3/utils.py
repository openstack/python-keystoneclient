import json
import uuid
import time
import urlparse

import httplib2
import mox
import unittest2 as unittest

from keystoneclient.v3 import client


def parameterize(ref):
    """Rewrites attributes to match the kwarg naming convention in client.

    >>> paramterize({'project_id': 0})
    {'project': 0}

    """
    params = ref.copy()
    for key in ref:
        if key[-3:] == '_id':
            params.setdefault(key[:-3], params.pop(key))
    return params


class TestCase(unittest.TestCase):
    TEST_TENANT_NAME = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'
    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v3')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v3')

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
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v3')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v3')

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


class CrudTests(object):
    key = None
    collection_key = None
    model = None
    manager = None

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

        self.headers['DELETE'] = self.headers['GET'].copy()
        self.headers['POST'] = self.headers['GET'].copy()
        self.headers['POST']['Content-Type'] = 'application/json'
        self.headers['PATCH'] = self.headers['POST'].copy()

    def serialize(self, entity):
        if isinstance(entity, dict):
            return json.dumps({self.key: entity}, sort_keys=True)
        if isinstance(entity, list):
            return json.dumps({self.collection_key: entity}, sort_keys=True)
        raise NotImplementedError('Are you sure you want to serialize that?')

    def test_create(self):
        ref = self.new_ref()
        resp = httplib2.Response({
            'status': 201,
            'body': self.serialize(ref),
        })

        method = 'POST'
        req_ref = ref.copy()
        req_ref.pop('id')
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/%s' % self.collection_key),
            method,
            body=self.serialize(req_ref),
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        returned = self.manager.create(**parameterize(req_ref))
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_get(self):
        ref = self.new_ref()
        resp = httplib2.Response({
            'status': 200,
            'body': self.serialize(ref),
        })
        method = 'GET'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/%s/%s' % (self.collection_key, ref['id'])),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        returned = self.manager.get(ref['id'])
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_list(self):
        ref_list = [self.new_ref(), self.new_ref()]

        resp = httplib2.Response({
            'status': 200,
            'body': self.serialize(ref_list),
        })

        method = 'GET'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/%s' % self.collection_key),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        returned_list = self.manager.list()
        self.assertTrue(len(returned_list))
        [self.assertTrue(isinstance(r, self.model)) for r in returned_list]

    def test_update(self):
        ref = self.new_ref()
        req_ref = ref.copy()
        del req_ref['id']

        resp = httplib2.Response({
            'status': 200,
            'body': self.serialize(ref),
        })

        method = 'PATCH'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/%s/%s' % (self.collection_key, ref['id'])),
            method,
            body=self.serialize(req_ref),
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        returned = self.manager.update(ref['id'], **parameterize(req_ref))
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_delete(self):
        ref = self.new_ref()
        method = 'DELETE'
        resp = httplib2.Response({
            'status': 204,
            'body': '',
        })
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/%s/%s' % (self.collection_key, ref['id'])),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.manager.delete(ref['id'])
