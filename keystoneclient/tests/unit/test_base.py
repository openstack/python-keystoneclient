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

from keystoneauth1.identity import v2
from keystoneauth1 import session
from oslotest import mockpatch

from keystoneclient import base
from keystoneclient.tests.unit import utils
from keystoneclient.v2_0 import client
from keystoneclient.v2_0 import roles


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

        self.useFixture(mockpatch.PatchObject(
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
        get_mock = self.useFixture(mockpatch.PatchObject(
            self.client, 'get', autospec=True, return_value=(None, self.body))
        ).mock
        rsrc = self.mgr._get(self.url, "hello")
        get_mock.assert_called_once_with(self.url)
        self.assertEqual(rsrc.hi, 1)

    def test_post(self):
        post_mock = self.useFixture(mockpatch.PatchObject(
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
        put_mock = self.useFixture(mockpatch.PatchObject(
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
        patch_mock = self.useFixture(mockpatch.PatchObject(
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
        patch_mock = self.useFixture(mockpatch.PatchObject(
            self.client, 'patch', autospec=True,
            return_value=(None, self.body))
        ).mock

        put_mock = self.useFixture(mockpatch.PatchObject(
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
