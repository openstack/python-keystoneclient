# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC
#
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

import copy
import urlparse
import uuid

import requests

from keystoneclient import exceptions
from keystoneclient.v3 import users
from tests.v3 import utils


class UserTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(UserTests, self).setUp()
        self.additionalSetUp()
        self.key = 'user'
        self.collection_key = 'users'
        self.model = users.User
        self.manager = self.client.users

    def new_ref(self, **kwargs):
        kwargs = super(UserTests, self).new_ref(**kwargs)
        kwargs.setdefault('description', uuid.uuid4().hex)
        kwargs.setdefault('domain_id', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('default_project_id', uuid.uuid4().hex)
        return kwargs

    def test_add_user_to_group(self):
        group_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 204,
            "text": '',
        })

        method = 'PUT'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/groups/%s/%s/%s' % (
                    group_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.add_to_group(user=ref['id'], group=group_id)
        self.assertRaises(exceptions.ValidationError,
                          self.manager.remove_from_group,
                          user=ref['id'],
                          group=None)

    def test_list_users_in_group(self):
        group_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]
        resp = utils.TestResponse({
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
                'v3/groups/%s/%s' % (
                    group_id, self.collection_key)),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned_list = self.manager.list(group=group_id)
        self.assertTrue(len(returned_list))
        [self.assertTrue(isinstance(r, self.model)) for r in returned_list]

    def test_check_user_in_group(self):
        group_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 204,
            "text": '',
        })

        method = 'HEAD'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/groups/%s/%s/%s' % (
                    group_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.check_in_group(user=ref['id'], group=group_id)

        self.assertRaises(exceptions.ValidationError,
                          self.manager.check_in_group,
                          user=ref['id'],
                          group=None)

    def test_remove_user_from_group(self):
        group_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
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
                'v3/groups/%s/%s/%s' % (
                    group_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.remove_from_group(user=ref['id'], group=group_id)
        self.assertRaises(exceptions.ValidationError,
                          self.manager.remove_from_group,
                          user=ref['id'],
                          group=None)

    def test_create_with_project(self):
        # Can create a user with the deprecated project option rather than
        # default_project_id.
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 201,
            "text": self.serialize(ref),
        })

        method = 'POST'
        req_ref = ref.copy()
        req_ref.pop('id')
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        kwargs['data'] = self.serialize(req_ref)
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/%s' % self.collection_key),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        param_ref = req_ref.copy()
        # Use deprecated project_id rather than new default_project_id.
        param_ref['project_id'] = param_ref.pop('default_project_id')
        params = utils.parameterize(param_ref)

        returned = self.manager.create(**params)
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_create_with_project_and_default_project(self):
        # Can create a user with the deprecated project and default_project_id.
        # The backend call should only pass the default_project_id.
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 201,
            "text": self.serialize(ref),
        })

        method = 'POST'
        req_ref = ref.copy()
        req_ref.pop('id')
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        kwargs['data'] = self.serialize(req_ref)
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/%s' % self.collection_key),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        param_ref = req_ref.copy()
        # Add the deprecated project_id in the call, the value will be ignored.
        param_ref['project_id'] = 'project'
        params = utils.parameterize(param_ref)

        returned = self.manager.create(**params)
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_update_with_project(self):
        # Can update a user with the deprecated project option rather than
        # default_project_id.
        ref = self.new_ref()
        req_ref = ref.copy()
        del req_ref['id']
        resp = utils.TestResponse({
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
                'v3/%s/%s' % (self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        param_ref = req_ref.copy()
        # Use deprecated project_id rather than new default_project_id.
        param_ref['project_id'] = param_ref.pop('default_project_id')
        params = utils.parameterize(param_ref)

        returned = self.manager.update(ref['id'], **params)
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)

    def test_update_with_project_and_default_project(self, ref=None):
        ref = self.new_ref()
        req_ref = ref.copy()
        del req_ref['id']
        resp = utils.TestResponse({
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
                'v3/%s/%s' % (self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        param_ref = req_ref.copy()
        # Add the deprecated project_id in the call, the value will be ignored.
        param_ref['project_id'] = 'project'
        params = utils.parameterize(param_ref)

        returned = self.manager.update(ref['id'], **params)
        self.assertTrue(isinstance(returned, self.model))
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)
