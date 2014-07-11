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

import functools

import mock
from oslo.config import cfg
import six

from keystoneclient.auth import base
from keystoneclient.tests import utils


class MockPlugin(base.BaseAuthPlugin):

    INT_DESC = 'test int'
    FLOAT_DESC = 'test float'
    BOOL_DESC = 'test bool'

    def __init__(self, **kwargs):
        self._data = kwargs

    def __getitem__(self, key):
        return self._data[key]

    def get_token(self, *args, **kwargs):
        return 'aToken'

    def get_endpoint(self, *args, **kwargs):
        return 'http://test'

    @classmethod
    def get_options(cls):
        return [
            cfg.IntOpt('a-int', default='3', help=cls.INT_DESC),
            cfg.BoolOpt('a-bool', help=cls.BOOL_DESC),
            cfg.FloatOpt('a-float', help=cls.FLOAT_DESC),
        ]


class MockManager(object):

    def __init__(self, driver):
        self.driver = driver


def mock_plugin(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        with mock.patch.object(base, 'get_plugin_class') as m:
            m.return_value = MockPlugin
            args = list(args) + [m]
            return f(*args, **kwargs)

    return inner


class TestCase(utils.TestCase):

    GROUP = 'auth'
    V2PASS = 'v2password'
    V3TOKEN = 'v3token'

    a_int = 88
    a_float = 88.8
    a_bool = False

    TEST_VALS = {'a_int': a_int,
                 'a_float': a_float,
                 'a_bool': a_bool}

    def assertTestVals(self, plugin, vals=TEST_VALS):
        for k, v in six.iteritems(vals):
            self.assertEqual(v, plugin[k])
