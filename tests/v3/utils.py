# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import urlparse
import uuid

import httpretty

from keystoneclient.openstack.common import jsonutils
from keystoneclient.v3 import client

from tests import utils

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


class UnauthenticatedTestCase(utils.TestCase):
    """Class used as base for unauthenticated calls."""

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v3')
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'
    TEST_ADMIN_URL = '%s%s' % (TEST_ROOT_ADMIN_URL, 'v3')


class TestCase(UnauthenticatedTestCase):

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
        self.client = client.Client(username=self.TEST_USER,
                                    token=self.TEST_TOKEN,
                                    tenant_name=self.TEST_TENANT_NAME,
                                    auth_url=self.TEST_URL,
                                    endpoint=self.TEST_URL)

    def stub_auth(self, subject_token=None, **kwargs):
        if not subject_token:
            subject_token = self.TEST_TOKEN

        self.stub_url(httpretty.POST, ['auth', 'tokens'],
                      X_Subject_Token=subject_token, **kwargs)


class CrudTests(object):
    key = None
    collection_key = None
    model = None
    manager = None
    path_prefix = None

    def new_ref(self, **kwargs):
        kwargs.setdefault('id', uuid.uuid4().hex)
        return kwargs

    def encode(self, entity):
        if isinstance(entity, dict):
            return {self.key: entity}
        if isinstance(entity, list):
            return {self.collection_key: entity}
        raise NotImplementedError('Are you sure you want to encode that?')

    def stub_entity(self, method, parts=None, entity=None, id=None, **kwargs):
        if entity:
            entity = self.encode(entity)
            kwargs['json'] = entity

        if not parts:
            parts = [self.collection_key]

            if self.path_prefix:
                parts.insert(0, self.path_prefix)

        if id:
            if not parts:
                parts = []

            parts.append(id)

        self.stub_url(method, parts=parts, **kwargs)

    def assertEntityRequestBodyIs(self, entity):
        self.assertRequestBodyIs(json=self.encode(entity))

    @httpretty.activate
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

        self.stub_entity(httpretty.POST, entity=req_ref, status=201)

        returned = self.manager.create(**parameterize(manager_ref))
        self.assertTrue(isinstance(returned, self.model))
        for attr in req_ref:
            self.assertEqual(
                getattr(returned, attr),
                req_ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)

    @httpretty.activate
    def test_get(self, ref=None):
        ref = ref or self.new_ref()

        self.stub_entity(httpretty.GET, id=ref['id'], entity=ref)

        returned = self.manager.get(ref['id'])
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    @httpretty.activate
    def test_list(self, ref_list=None, expected_path=None, **filter_kwargs):
        ref_list = ref_list or [self.new_ref(), self.new_ref()]

        if not expected_path:
            if self.path_prefix:
                expected_path = 'v3/%s/%s' % (self.path_prefix,
                                              self.collection_key)
            else:
                expected_path = 'v3/%s' % self.collection_key

        httpretty.register_uri(httpretty.GET,
                               urlparse.urljoin(self.TEST_URL, expected_path),
                               body=jsonutils.dumps(self.encode(ref_list)))

        returned_list = self.manager.list(**filter_kwargs)
        self.assertTrue(len(returned_list))
        [self.assertTrue(isinstance(r, self.model)) for r in returned_list]

    @httpretty.activate
    def test_find(self, ref=None):
        ref = ref or self.new_ref()
        ref_list = [ref]

        self.stub_entity(httpretty.GET, entity=ref_list)

        returned = self.manager.find(name=getattr(ref, 'name', None))
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

        if hasattr(ref, 'name'):
            self.assertQueryStringIs({'name': ref['name']})
        else:
            self.assertQueryStringIs({})

    @httpretty.activate
    def test_update(self, ref=None):
        ref = ref or self.new_ref()

        self.stub_entity(httpretty.PATCH, id=ref['id'], entity=ref)

        req_ref = ref.copy()
        req_ref.pop('id')

        returned = self.manager.update(ref['id'], **parameterize(req_ref))
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(req_ref)

    @httpretty.activate
    def test_delete(self, ref=None):
        ref = ref or self.new_ref()

        self.stub_entity(httpretty.DELETE, id=ref['id'], status=204)
        self.manager.delete(ref['id'])
