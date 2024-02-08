# -*- coding: utf-8 -*-
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid

import fixtures
from keystoneauth1.identity import v2
from keystoneauth1 import session
import requests

from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient.tests.unit import utils
from keystoneclient import utils as base_utils
from keystoneclient.v2_0 import client
from keystoneclient.v2_0 import roles
from keystoneclient.v3 import users

TEST_REQUEST_ID = uuid.uuid4().hex
TEST_REQUEST_ID_1 = uuid.uuid4().hex


def create_response_with_request_id_header():
    resp = requests.Response()
    resp.headers['x-openstack-request-id'] = TEST_REQUEST_ID
    return resp


class HumanReadable(base.Resource):
    HUMAN_ID = True


class BaseTest(utils.TestCase):

    def test_resource_repr(self):
        r = base.Resource(None, dict(foo="bar", baz="spam"))
        self.assertEqual(repr(r), "<Resource baz=spam, foo=bar>")

    def test_getid(self):
        self.assertEqual(base.getid(4), 4)

        class TmpObject(object):
            id = 4
        self.assertEqual(base.getid(TmpObject), 4)

    def test_resource_lazy_getattr(self):
        auth = v2.Token(token=self.TEST_TOKEN,
                        auth_url='http://127.0.0.1:5000')
        session_ = session.Session(auth=auth)
        self.client = client.Client(session=session_)

        self.useFixture(fixtures.MockPatchObject(
            self.client._adapter, 'get', side_effect=AttributeError,
            autospec=True))

        f = roles.Role(self.client.roles, {'id': 1, 'name': 'Member'})
        self.assertEqual(f.name, 'Member')

        # Missing stuff still fails after a second get
        self.assertRaises(AttributeError, getattr, f, 'blahblah')

    def test_eq(self):
        # Two resources with same ID: never equal if their info is not equal
        r1 = base.Resource(None, {'id': 1, 'name': 'hi'})
        r2 = base.Resource(None, {'id': 1, 'name': 'hello'})
        self.assertNotEqual(r1, r2)
        self.assertTrue(r1 != r2)

        # Two resources with same ID: equal if their info is equal
        # The truth of r1==r2 does not imply that r1!=r2 is false in PY2.
        # Test that inequality operator is defined and that comparing equal
        # items returns False
        r1 = base.Resource(None, {'id': 1, 'name': 'hello'})
        r2 = base.Resource(None, {'id': 1, 'name': 'hello'})
        self.assertTrue(r1 == r2)
        self.assertFalse(r1 != r2)

        # Two resources of different types: never equal
        r1 = base.Resource(None, {'id': 1})
        r2 = roles.Role(None, {'id': 1})
        self.assertNotEqual(r1, r2)
        self.assertTrue(r1 != r2)

        # Two resources with no ID: equal if their info is equal
        # The truth of r1==r2 does not imply that r1!=r2 is false in PY2.
        # Test that inequality operator is defined and that comparing equal
        # items returns False.
        r1 = base.Resource(None, {'name': 'joe', 'age': 12})
        r2 = base.Resource(None, {'name': 'joe', 'age': 12})
        self.assertTrue(r1 == r2)
        self.assertFalse(r1 != r2)

        r1 = base.Resource(None, {'id': 1})
        self.assertNotEqual(r1, object())
        self.assertTrue(r1 != object())
        self.assertNotEqual(r1, {'id': 1})
        self.assertTrue(r1 != {'id': 1})

    def test_human_id(self):
        r = base.Resource(None, {"name": "1 of !"})
        self.assertIsNone(r.human_id)
        r = HumanReadable(None, {"name": "1 of !"})
        self.assertEqual(r.human_id, "1-of")

    def test_non_ascii_attr(self):
        r_dict = {"name": "foobar",
                  u"тест": "1234",
                  u"тест2": u"привет мир"}

        r = base.Resource(None, r_dict)
        self.assertEqual(r.name, "foobar")
        self.assertEqual(r.to_dict(), r_dict)


class ManagerTest(utils.TestCase):
    body = {"hello": {"hi": 1}}
    url = "/test-url"

    def setUp(self):
        super(ManagerTest, self).setUp()

        auth = v2.Token(auth_url='http://127.0.0.1:5000',
                        token=self.TEST_TOKEN)
        session_ = session.Session(auth=auth)
        self.client = client.Client(session=session_)._adapter

        self.mgr = base.Manager(self.client)
        self.mgr.resource_class = base.Resource

    def test_api(self):
        with self.deprecations.expect_deprecations_here():
            self.assertEqual(self.mgr.api, self.client)

    def test_get(self):
        get_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'get', autospec=True, return_value=(None, self.body))
        ).mock
        rsrc = self.mgr._get(self.url, "hello")
        get_mock.assert_called_once_with(self.url)
        self.assertEqual(rsrc.hi, 1)

    def test_post(self):
        post_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'post', autospec=True, return_value=(None, self.body))
        ).mock

        rsrc = self.mgr._post(self.url, self.body, "hello")
        post_mock.assert_called_once_with(self.url, body=self.body)
        self.assertEqual(rsrc.hi, 1)

        post_mock.reset_mock()

        rsrc = self.mgr._post(self.url, self.body, "hello", return_raw=True)
        post_mock.assert_called_once_with(self.url, body=self.body)
        self.assertEqual(rsrc["hi"], 1)

    def test_put(self):
        put_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'put', autospec=True, return_value=(None, self.body))
        ).mock

        rsrc = self.mgr._put(self.url, self.body, "hello")
        put_mock.assert_called_once_with(self.url, body=self.body)
        self.assertEqual(rsrc.hi, 1)

        put_mock.reset_mock()

        rsrc = self.mgr._put(self.url, self.body)
        put_mock.assert_called_once_with(self.url, body=self.body)
        self.assertEqual(rsrc.hello["hi"], 1)

    def test_patch(self):
        patch_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'patch', autospec=True,
            return_value=(None, self.body))
        ).mock

        rsrc = self.mgr._patch(self.url, self.body, "hello")
        patch_mock.assert_called_once_with(self.url, body=self.body)
        self.assertEqual(rsrc.hi, 1)

        patch_mock.reset_mock()

        rsrc = self.mgr._patch(self.url, self.body)
        patch_mock.assert_called_once_with(self.url, body=self.body)
        self.assertEqual(rsrc.hello["hi"], 1)

    def test_update(self):
        patch_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'patch', autospec=True,
            return_value=(None, self.body))
        ).mock

        put_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'put', autospec=True, return_value=(None, self.body))
        ).mock

        rsrc = self.mgr._update(
            self.url, body=self.body, response_key="hello", method="PATCH",
            management=False)
        patch_mock.assert_called_once_with(
            self.url, management=False, body=self.body)
        self.assertEqual(rsrc.hi, 1)

        rsrc = self.mgr._update(
            self.url, body=None, response_key="hello", method="PUT",
            management=True)
        put_mock.assert_called_once_with(self.url, management=True, body=None)
        self.assertEqual(rsrc.hi, 1)


class ManagerRequestIdTest(utils.TestCase):
    url = "/test-url"
    resp = create_response_with_request_id_header()

    def setUp(self):
        super(ManagerRequestIdTest, self).setUp()

        auth = v2.Token(auth_url='http://127.0.0.1:5000',
                        token=self.TEST_TOKEN)
        session_ = session.Session(auth=auth)
        self.client = client.Client(session=session_,
                                    include_metadata='True')._adapter

        self.mgr = base.Manager(self.client)
        self.mgr.resource_class = base.Resource

    def mock_request_method(self, request_method, body):
        return self.useFixture(fixtures.MockPatchObject(
            self.client, request_method, autospec=True,
            return_value=(self.resp, body))
        ).mock

    def test_get(self):
        body = {"hello": {"hi": 1}}
        get_mock = self.mock_request_method('get', body)
        rsrc = self.mgr._get(self.url, "hello")
        get_mock.assert_called_once_with(self.url)
        self.assertEqual(rsrc.data.hi, 1)
        self.assertEqual(rsrc.request_ids[0], TEST_REQUEST_ID)

    def test_list(self):
        body = {"hello": [{"name": "admin"}, {"name": "admin"}]}
        get_mock = self.mock_request_method('get', body)

        returned_list = self.mgr._list(self.url, "hello")
        self.assertEqual(returned_list.request_ids[0], TEST_REQUEST_ID)
        get_mock.assert_called_once_with(self.url)

    def test_list_with_multiple_response_objects(self):
        body = {"hello": [{"name": "admin"}, {"name": "admin"}]}
        resp_1 = requests.Response()
        resp_1.headers['x-openstack-request-id'] = TEST_REQUEST_ID
        resp_2 = requests.Response()
        resp_2.headers['x-openstack-request-id'] = TEST_REQUEST_ID_1

        resp_result = [resp_1, resp_2]
        get_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'get', autospec=True,
            return_value=(resp_result, body))
        ).mock

        returned_list = self.mgr._list(self.url, "hello")
        self.assertIn(returned_list.request_ids[0], [
            TEST_REQUEST_ID, TEST_REQUEST_ID_1])
        self.assertIn(returned_list.request_ids[1], [
            TEST_REQUEST_ID, TEST_REQUEST_ID_1])
        get_mock.assert_called_once_with(self.url)

    def test_post(self):
        body = {"hello": {"hi": 1}}
        post_mock = self.mock_request_method('post', body)
        rsrc = self.mgr._post(self.url, body, "hello")
        post_mock.assert_called_once_with(self.url, body=body)
        self.assertEqual(rsrc.data.hi, 1)

        post_mock.reset_mock()

        rsrc = self.mgr._post(self.url, body, "hello", return_raw=True)
        post_mock.assert_called_once_with(self.url, body=body)
        self.assertNotIsInstance(rsrc, base.Response)
        self.assertEqual(rsrc["hi"], 1)

    def test_put(self):
        body = {"hello": {"hi": 1}}
        put_mock = self.mock_request_method('put', body)
        rsrc = self.mgr._put(self.url, body, "hello")
        put_mock.assert_called_once_with(self.url, body=body)
        self.assertEqual(rsrc.data.hi, 1)

        put_mock.reset_mock()

        rsrc = self.mgr._put(self.url, body)
        put_mock.assert_called_once_with(self.url, body=body)
        self.assertEqual(rsrc.data.hello["hi"], 1)
        self.assertEqual(rsrc.request_ids[0], TEST_REQUEST_ID)

    def test_head(self):
        get_mock = self.mock_request_method('head', None)
        rsrc = self.mgr._head(self.url)
        get_mock.assert_called_once_with(self.url)
        self.assertFalse(rsrc.data)
        self.assertEqual(rsrc.request_ids[0], TEST_REQUEST_ID)

    def test_delete(self):
        delete_mock = self.mock_request_method('delete', None)
        resp, base_resp = self.mgr._delete(self.url, name="hello")

        delete_mock.assert_called_once_with('/test-url', name='hello')
        self.assertEqual(base_resp.request_ids[0], TEST_REQUEST_ID)
        self.assertEqual(base_resp.data, None)
        self.assertIsInstance(resp, requests.Response)

    def test_patch(self):
        body = {"hello": {"hi": 1}}
        patch_mock = self.mock_request_method('patch', body)
        rsrc = self.mgr._patch(self.url, body, "hello")
        patch_mock.assert_called_once_with(self.url, body=body)
        self.assertEqual(rsrc.data.hi, 1)

        patch_mock.reset_mock()

        rsrc = self.mgr._patch(self.url, body)
        patch_mock.assert_called_once_with(self.url, body=body)
        self.assertEqual(rsrc.data.hello["hi"], 1)
        self.assertEqual(rsrc.request_ids[0], TEST_REQUEST_ID)

    def test_update(self):
        body = {"hello": {"hi": 1}}
        patch_mock = self.mock_request_method('patch', body)
        put_mock = self.mock_request_method('put', body)

        rsrc = self.mgr._update(
            self.url, body=body, response_key="hello", method="PATCH",
            management=False)
        patch_mock.assert_called_once_with(
            self.url, management=False, body=body)
        self.assertEqual(rsrc.data.hi, 1)

        rsrc = self.mgr._update(
            self.url, body=None, response_key="hello", method="PUT",
            management=True)
        put_mock.assert_called_once_with(self.url, management=True, body=None)
        self.assertEqual(rsrc.data.hi, 1)
        self.assertEqual(rsrc.request_ids[0], TEST_REQUEST_ID)


class ManagerWithFindRequestIdTest(utils.TestCase):
    url = "/fakes"
    resp = create_response_with_request_id_header()

    def setUp(self):
        super(ManagerWithFindRequestIdTest, self).setUp()

        auth = v2.Token(auth_url='http://127.0.0.1:5000',
                        token=self.TEST_TOKEN)
        session_ = session.Session(auth=auth)
        self.client = client.Client(session=session_,
                                    include_metadata='True')._adapter

    def test_find_resource(self):
        body = {"roles": [{"name": 'entity_one'}, {"name": 'entity_one_1'}]}
        request_resp = requests.Response()
        request_resp.headers['x-openstack-request-id'] = TEST_REQUEST_ID

        get_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'get', autospec=True,
            side_effect=[exceptions.NotFound, (request_resp, body)])
        ).mock

        mgr = roles.RoleManager(self.client)
        mgr.resource_class = roles.Role
        response = base_utils.find_resource(mgr, 'entity_one')
        get_mock.assert_called_with('/OS-KSADM/roles')
        self.assertEqual(response.request_ids[0], TEST_REQUEST_ID)


class CrudManagerRequestIdTest(utils.TestCase):
    resp = create_response_with_request_id_header()
    request_resp = requests.Response()
    request_resp.headers['x-openstack-request-id'] = TEST_REQUEST_ID

    def setUp(self):
        super(CrudManagerRequestIdTest, self).setUp()

        auth = v2.Token(auth_url='http://127.0.0.1:5000',
                        token=self.TEST_TOKEN)
        session_ = session.Session(auth=auth)
        self.client = client.Client(session=session_,
                                    include_metadata='True')._adapter

    def test_find_resource(self):
        body = {"users": [{"name": 'entity_one'}]}
        get_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'get', autospec=True,
            side_effect=[exceptions.NotFound, (self.request_resp, body)])
        ).mock
        mgr = users.UserManager(self.client)
        mgr.resource_class = users.User
        response = base_utils.find_resource(mgr, 'entity_one')
        get_mock.assert_called_with('/users?name=entity_one')
        self.assertEqual(response.request_ids[0], TEST_REQUEST_ID)

    def test_list(self):
        body = {"users": [{"name": "admin"}, {"name": "admin"}]}

        get_mock = self.useFixture(fixtures.MockPatchObject(
            self.client, 'get', autospec=True,
            return_value=(self.request_resp, body))
        ).mock
        mgr = users.UserManager(self.client)
        mgr.resource_class = users.User
        returned_list = mgr.list()
        self.assertEqual(returned_list.request_ids[0], TEST_REQUEST_ID)
        get_mock.assert_called_once_with('/users?')
