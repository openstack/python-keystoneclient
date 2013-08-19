# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from keystoneclient import exceptions
from keystoneclient import utils
from tests import utils as test_utils


class FakeResource(object):
    pass


class FakeManager(object):

    resource_class = FakeResource

    resources = {
        '1234': {'name': 'entity_one'},
        '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0': {'name': 'entity_two'},
        '5678': {'name': '9876'}
    }

    def get(self, resource_id):
        try:
            return self.resources[str(resource_id)]
        except KeyError:
            raise exceptions.NotFound(resource_id)

    def find(self, name=None):
        if name == '9999':
            # NOTE(morganfainberg): special case that raises NoUniqueMatch.
            raise exceptions.NoUniqueMatch()
        for resource_id, resource in self.resources.items():
            if resource['name'] == str(name):
                return resource
        raise exceptions.NotFound(name)


class FindResourceTestCase(test_utils.TestCase):

    def setUp(self):
        super(FindResourceTestCase, self).setUp()
        self.manager = FakeManager()

    def test_find_none(self):
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          'asdf')

    def test_find_by_integer_id(self):
        output = utils.find_resource(self.manager, 1234)
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_str_id(self):
        output = utils.find_resource(self.manager, '1234')
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_uuid(self):
        uuid = '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0'
        output = utils.find_resource(self.manager, uuid)
        self.assertEqual(output, self.manager.resources[uuid])

    def test_find_by_str_name(self):
        output = utils.find_resource(self.manager, 'entity_one')
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_int_name(self):
        output = utils.find_resource(self.manager, 9876)
        self.assertEqual(output, self.manager.resources['5678'])

    def test_find_no_unique_match(self):
        self.assertRaises(exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          9999)
