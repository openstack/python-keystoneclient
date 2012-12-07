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
        kwargs.setdefault('project_id', uuid.uuid4().hex)
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
