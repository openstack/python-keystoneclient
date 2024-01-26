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

from keystoneauth1 import exceptions as ksa_exceptions
import testresources
from testtools import matchers


from keystoneclient import exceptions as ksc_exceptions
from keystoneclient.tests.unit import client_fixtures
from keystoneclient.tests.unit import utils as test_utils
from keystoneclient import utils


class FakeResource(object):
    pass


class FakeManager(object):

    resource_class = FakeResource

    resources = {
        '1234': {'name': 'entity_one'},
        '8e8ec658-c7b0-4243-bdf8-6f7f2952c0d0': {'name': 'entity_two'},
        '\xe3\x82\xbdtest': {'name': '\u30bdtest'},
        '5678': {'name': '9876'}
    }

    def get(self, resource_id):
        try:
            return self.resources[str(resource_id)]
        except KeyError:
            raise ksa_exceptions.NotFound(resource_id)

    def find(self, name=None):
        if name == '9999':
            # NOTE(morganfainberg): special case that raises NoUniqueMatch.
            raise ksc_exceptions.NoUniqueMatch()
        for resource_id, resource in self.resources.items():
            if resource['name'] == str(name):
                return resource
        raise ksa_exceptions.NotFound(name)


class FindResourceTestCase(test_utils.TestCase):

    def setUp(self):
        super(FindResourceTestCase, self).setUp()
        self.manager = FakeManager()

    def test_find_none(self):
        self.assertRaises(ksc_exceptions.CommandError,
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

    def test_find_by_unicode(self):
        name = '\xe3\x82\xbdtest'
        output = utils.find_resource(self.manager, name)
        self.assertEqual(output, self.manager.resources[name])

    def test_find_by_str_name(self):
        output = utils.find_resource(self.manager, 'entity_one')
        self.assertEqual(output, self.manager.resources['1234'])

    def test_find_by_int_name(self):
        output = utils.find_resource(self.manager, 9876)
        self.assertEqual(output, self.manager.resources['5678'])

    def test_find_no_unique_match(self):
        self.assertRaises(ksc_exceptions.CommandError,
                          utils.find_resource,
                          self.manager,
                          9999)


class FakeObject(object):
    def __init__(self, name):
        self.name = name


class HashSignedTokenTestCase(test_utils.TestCase,
                              testresources.ResourcedTestCase):
    """Unit tests for utils.hash_signed_token()."""

    resources = [('examples', client_fixtures.EXAMPLES_RESOURCE)]

    def test_default_md5(self):
        """The default hash method is md5."""
        token = self.examples.SIGNED_TOKEN_SCOPED
        token = token.encode('utf-8')
        token_id_default = utils.hash_signed_token(token)
        token_id_md5 = utils.hash_signed_token(token, mode='md5')
        self.assertThat(token_id_default, matchers.Equals(token_id_md5))
        # md5 hash is 32 chars.
        self.assertThat(token_id_default, matchers.HasLength(32))

    def test_sha256(self):
        """Can also hash with sha256."""
        token = self.examples.SIGNED_TOKEN_SCOPED
        token = token.encode('utf-8')
        token_id = utils.hash_signed_token(token, mode='sha256')
        # sha256 hash is 64 chars.
        self.assertThat(token_id, matchers.HasLength(64))


def load_tests(loader, tests, pattern):
    return testresources.OptimisingTestSuite(tests)
