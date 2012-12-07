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

from keystoneclient.v3 import groups
from tests.v3 import utils


class GroupTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(GroupTests, self).setUp()
        self.additionalSetUp()
        self.key = 'group'
        self.collection_key = 'groups'
        self.model = groups.Group
        self.manager = self.client.groups

    def new_ref(self, **kwargs):
        kwargs = super(GroupTests, self).new_ref(**kwargs)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs

    def test_list_groups_for_user(self):
        user_id = uuid.uuid4().hex
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
                'v3/users/%s/%s' % (
                    user_id, self.collection_key)),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned_list = self.manager.list(user=user_id)
        self.assertTrue(len(returned_list))
        [self.assertTrue(isinstance(r, self.model)) for r in returned_list]
