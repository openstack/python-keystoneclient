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

import datetime
import iso8601
import os
import shutil
import string
import sys
import tempfile
import testtools

import fixtures
import webob

from keystoneclient.common import cms
from keystoneclient.middleware import auth_token
from keystoneclient.openstack.common import jsonutils
from keystoneclient.openstack.common import memorycache
from keystoneclient.openstack.common import timeutils
from keystoneclient import utils


ROOTDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

CERTDIR = os.path.join(ROOTDIR, "examples/pki/certs")
KEYDIR = os.path.join(ROOTDIR, "examples/pki/private")
CMSDIR = os.path.join(ROOTDIR, "examples/pki/cms")
SIGNING_CERT = os.path.join(CERTDIR, 'signing_cert.pem')
SIGNING_KEY = os.path.join(KEYDIR, 'signing_key.pem')
CA = os.path.join(CERTDIR, 'ca.pem')

REVOCATION_LIST = None
REVOKED_TOKEN = None
REVOKED_TOKEN_HASH = None
REVOKED_v3_TOKEN = None
REVOKED_v3_TOKEN_HASH = None
SIGNED_REVOCATION_LIST = None
SIGNED_TOKEN_SCOPED = None
SIGNED_TOKEN_UNSCOPED = None
SIGNED_v3_TOKEN_SCOPED = None
SIGNED_v3_TOKEN_UNSCOPED = None
SIGNED_TOKEN_SCOPED_KEY = None
SIGNED_TOKEN_UNSCOPED_KEY = None
SIGNED_v3_TOKEN_SCOPED_KEY = None

VALID_SIGNED_REVOCATION_LIST = None

UUID_TOKEN_DEFAULT = "ec6c0710ec2f471498484c1b53ab4f9d"
UUID_TOKEN_NO_SERVICE_CATALOG = '8286720fbe4941e69fa8241723bb02df'
UUID_TOKEN_UNSCOPED = '731f903721c14827be7b2dc912af7776'
VALID_DIABLO_TOKEN = 'b0cf19b55dbb4f20a6ee18e6c6cf1726'
v3_UUID_TOKEN_DEFAULT = '5603457654b346fdbb93437bfe76f2f1'
v3_UUID_TOKEN_UNSCOPED = 'd34835fdaec447e695a0a024d84f8d79'
v3_UUID_TOKEN_DOMAIN_SCOPED = 'e8a7b63aaa4449f38f0c5c05c3581792'

INVALID_SIGNED_TOKEN = string.replace(
    """AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
0000000000000000000000000000000000000000000000000000000000000000
1111111111111111111111111111111111111111111111111111111111111111
2222222222222222222222222222222222222222222222222222222222222222
3333333333333333333333333333333333333333333333333333333333333333
4444444444444444444444444444444444444444444444444444444444444444
5555555555555555555555555555555555555555555555555555555555555555
6666666666666666666666666666666666666666666666666666666666666666
7777777777777777777777777777777777777777777777777777777777777777
8888888888888888888888888888888888888888888888888888888888888888
9999999999999999999999999999999999999999999999999999999999999999
0000000000000000000000000000000000000000000000000000000000000000
xg==""", "\n", "")

# JSON responses keyed by token ID
TOKEN_RESPONSES = {
    UUID_TOKEN_DEFAULT: {
        'access': {
            'token': {
                'id': UUID_TOKEN_DEFAULT,
                'expires': '2020-01-01T00:00:10.000123Z',
                'tenant': {
                    'id': 'tenant_id1',
                    'name': 'tenant_name1',
                },
            },
            'user': {
                'id': 'user_id1',
                'name': 'user_name1',
                'roles': [
                    {'name': 'role1'},
                    {'name': 'role2'},
                ],
            },
            'serviceCatalog': {}
        },
    },
    VALID_DIABLO_TOKEN: {
        'access': {
            'token': {
                'id': VALID_DIABLO_TOKEN,
                'expires': '2020-01-01T00:00:10.000123Z',
                'tenantId': 'tenant_id1',
            },
            'user': {
                'id': 'user_id1',
                'name': 'user_name1',
                'roles': [
                    {'name': 'role1'},
                    {'name': 'role2'},
                ],
            },
        },
    },
    UUID_TOKEN_UNSCOPED: {
        'access': {
            'token': {
                'id': UUID_TOKEN_UNSCOPED,
                'expires': '2020-01-01T00:00:10.000123Z',
            },
            'user': {
                'id': 'user_id1',
                'name': 'user_name1',
                'roles': [
                    {'name': 'role1'},
                    {'name': 'role2'},
                ],
            },
        },
    },
    UUID_TOKEN_NO_SERVICE_CATALOG: {
        'access': {
            'token': {
                'id': 'valid-token',
                'expires': '2020-01-01T00:00:10.000123Z',
                'tenant': {
                    'id': 'tenant_id1',
                    'name': 'tenant_name1',
                },
            },
            'user': {
                'id': 'user_id1',
                'name': 'user_name1',
                'roles': [
                    {'name': 'role1'},
                    {'name': 'role2'},
                ],
            }
        },
    },
    v3_UUID_TOKEN_DEFAULT: {
        'token': {
            'expires_at': '2020-01-01T00:00:10.000123Z',
            'user': {
                'id': 'user_id1',
                'name': 'user_name1',
                'domain': {
                    'id': 'domain_id1',
                    'name': 'domain_name1'
                }
            },
            'project': {
                'id': 'tenant_id1',
                'name': 'tenant_name1',
                'domain': {
                    'id': 'domain_id1',
                    'name': 'domain_name1'
                }
            },
            'roles': [
                {'name': 'role1', 'id': 'Role1'},
                {'name': 'role2', 'id': 'Role2'},
            ],
            'catalog': {}
        }
    },
    v3_UUID_TOKEN_UNSCOPED: {
        'token': {
            'expires_at': '2020-01-01T00:00:10.000123Z',
            'user': {
                'id': 'user_id1',
                'name': 'user_name1',
                'domain': {
                    'id': 'domain_id1',
                    'name': 'domain_name1'
                }
            }
        }
    },
    v3_UUID_TOKEN_DOMAIN_SCOPED: {
        'token': {
            'expires_at': '2020-01-01T00:00:10.000123Z',
            'user': {
                'id': 'user_id1',
                'name': 'user_name1',
                'domain': {
                    'id': 'domain_id1',
                    'name': 'domain_name1'
                }
            },
            'domain': {
                'id': 'domain_id1',
                'name': 'domain_name1',
            },
            'roles': [
                {'name': 'role1', 'id': 'Role1'},
                {'name': 'role2', 'id': 'Role2'},
            ],
            'catalog': {}
        }
    }
}

EXPECTED_V2_DEFAULT_ENV_RESPONSE = {
    'HTTP_X_IDENTITY_STATUS': 'Confirmed',
    'HTTP_X_TENANT_ID': 'tenant_id1',
    'HTTP_X_TENANT_NAME': 'tenant_name1',
    'HTTP_X_USER_ID': 'user_id1',
    'HTTP_X_USER_NAME': 'user_name1',
    'HTTP_X_ROLES': 'role1,role2',
    'HTTP_X_USER': 'user_name1',  # deprecated (diablo-compat)
    'HTTP_X_TENANT': 'tenant_name1',  # deprecated (diablo-compat)
    'HTTP_X_ROLE': 'role1,role2',  # deprecated (diablo-compat)
}

FAKE_RESPONSE_STACK = []


# @TODO(mordred) This should become a testresources resource attached to the
#                class
# The data for these tests are signed using openssl and are stored in files
# in the signing subdirectory.  In order to keep the values consistent between
# the tests and the signed documents, we read them in for use in the tests.
signing_path = CMSDIR
with open(os.path.join(signing_path, 'auth_token_scoped.pem')) as f:
    SIGNED_TOKEN_SCOPED = cms.cms_to_token(f.read())
with open(os.path.join(signing_path, 'auth_token_unscoped.pem')) as f:
    SIGNED_TOKEN_UNSCOPED = cms.cms_to_token(f.read())
with open(os.path.join(signing_path, 'auth_v3_token_scoped.pem')) as f:
    SIGNED_v3_TOKEN_SCOPED = cms.cms_to_token(f.read())
with open(os.path.join(signing_path, 'auth_token_revoked.pem')) as f:
    REVOKED_TOKEN = cms.cms_to_token(f.read())
with open(os.path.join(signing_path,
          'auth_token_scoped_expired.pem')) as f:
    SIGNED_TOKEN_SCOPED_EXPIRED = cms.cms_to_token(f.read())
REVOKED_TOKEN_HASH = utils.hash_signed_token(REVOKED_TOKEN)
with open(os.path.join(signing_path, 'auth_v3_token_revoked.pem')) as f:
    REVOKED_v3_TOKEN = cms.cms_to_token(f.read())
REVOKED_v3_TOKEN_HASH = utils.hash_signed_token(REVOKED_v3_TOKEN)
with open(os.path.join(signing_path, 'revocation_list.json')) as f:
    REVOCATION_LIST = jsonutils.loads(f.read())
with open(os.path.join(signing_path, 'revocation_list.pem')) as f:
    VALID_SIGNED_REVOCATION_LIST = jsonutils.dumps(
        {'signed': f.read()})
SIGNED_TOKEN_SCOPED_KEY =\
    cms.cms_hash_token(SIGNED_TOKEN_SCOPED)
SIGNED_TOKEN_UNSCOPED_KEY =\
    cms.cms_hash_token(SIGNED_TOKEN_UNSCOPED)
SIGNED_v3_TOKEN_SCOPED_KEY = (
    cms.cms_hash_token(SIGNED_v3_TOKEN_SCOPED))

TOKEN_RESPONSES[SIGNED_TOKEN_SCOPED_KEY] = {
    'access': {
        'token': {
            'id': SIGNED_TOKEN_SCOPED_KEY,
        },
        'user': {
            'id': 'user_id1',
            'name': 'user_name1',
            'tenantId': 'tenant_id1',
            'tenantName': 'tenant_name1',
            'roles': [
                {'name': 'role1'},
                {'name': 'role2'},
            ],
        },
    },
}

TOKEN_RESPONSES[SIGNED_TOKEN_UNSCOPED_KEY] = {
    'access': {
        'token': {
            'id': SIGNED_TOKEN_UNSCOPED_KEY,
        },
        'user': {
            'id': 'user_id1',
            'name': 'user_name1',
            'roles': [
                {'name': 'role1'},
                {'name': 'role2'},
            ],
        },
    },
}

TOKEN_RESPONSES[SIGNED_v3_TOKEN_SCOPED_KEY] = {
    'token': {
        'expires': '2020-01-01T00:00:10.000123Z',
        'user': {
            'id': 'user_id1',
            'name': 'user_name1',
            'domain': {
                'id': 'domain_id1',
                'name': 'domain_name1'
            }
        },
        'project': {
            'id': 'tenant_id1',
            'name': 'tenant_name1',
            'domain': {
                'id': 'domain_id1',
                'name': 'domain_name1'
            }
        },
        'roles': [
            {'name': 'role1'},
            {'name': 'role2'}
        ],
        'catalog': {}
    }
}

VERSION_LIST_v3 = {
    "versions": {
        "values": [
            {
                "id": "v3.0",
                "status": "stable",
                "updated": "2013-03-06T00:00:00Z",
                "links": []
            },
            {
                "id": "v2.0",
                "status": "beta",
                "updated": "2011-11-19T00:00:00Z",
                "links": []
            }
        ]
    }
}

VERSION_LIST_v2 = {
    "versions": {
        "values": [
            {
                "id": "v2.0",
                "status": "beta",
                "updated": "2011-11-19T00:00:00Z",
                "links": []
            }
        ]
    }
}


class NoModuleFinder(object):
    """Disallow further imports of 'module'."""

    def __init__(self, module):
        self.module = module

    def find_module(self, fullname, path):
        if fullname == self.module or fullname.startswith(self.module + '.'):
            raise ImportError


class DisableModuleFixture(fixtures.Fixture):
    """A fixture to provide support for unloading/disabling modules."""

    def __init__(self, module, *args, **kw):
        super(DisableModuleFixture, self).__init__(*args, **kw)
        self.module = module
        self._finders = []
        self._cleared_modules = {}

    def tearDown(self):
        super(DisableModuleFixture, self).tearDown()
        for finder in self._finders:
            sys.meta_path.remove(finder)
        sys.modules.update(self._cleared_modules)

    def clear_module(self):
        cleared_modules = {}
        for fullname in sys.modules.keys():
            if (fullname == self.module or
                    fullname.startswith(self.module + '.')):
                cleared_modules[fullname] = sys.modules.pop(fullname)
        return cleared_modules

    def setUp(self):
        """Ensure ImportError for the specified module."""

        super(DisableModuleFixture, self).setUp()

        # Clear 'module' references in sys.modules
        self._cleared_modules.update(self.clear_module())

        finder = NoModuleFinder(self.module)
        self._finders.append(finder)
        sys.meta_path.insert(0, finder)


class FakeSwiftOldMemcacheClient(memorycache.Client):
    # NOTE(vish,chmou): old swift memcache uses param timeout instead of time
    def set(self, key, value, timeout=0, min_compress_len=0):
        sup = super(FakeSwiftOldMemcacheClient, self)
        sup.set(key, value, timeout, min_compress_len)


class FakeHTTPResponse(object):
    def __init__(self, status, body):
        self.status = status
        self.body = body

    def read(self):
        return self.body


class BaseFakeHTTPConnection(object):

    def _user_token_responses(self, token_id):
        """Emulate user token responses.

        Return success if the token is in the list we know
        about. If the request is for revoked tokens, then return
        the revoked list, else if a different token is provided,
        return 404 indicating an unknown (therefore unauthorized) token.

        """
        if token_id in TOKEN_RESPONSES.keys():
            status = 200
            body = jsonutils.dumps(TOKEN_RESPONSES[token_id])
        elif token_id == "revoked":
            status = 200
            body = SIGNED_REVOCATION_LIST
        else:
            status = 404
            body = str()
        return status, body

    def fake_v2_responses(self, path):
        token_id = path.rsplit('/', 1)[1]
        return self._user_token_responses(token_id)

    def fake_v3_responses(self, path, **kwargs):
        headers = kwargs.get('headers')
        token_id = headers['X-Subject-Token']
        return self._user_token_responses(token_id)

    def fake_v2_admin_token(self, path):
        status = 200
        body = jsonutils.dumps({
            'access': {
                'token': {'id': 'admin_token2',
                          'expires': '2022-10-03T16:58:01Z'}
            },
        })
        return status, body


class FakeHTTPConnection(BaseFakeHTTPConnection):
    """Emulate a fake Keystone v2 server."""

    def __init__(self, *args, **kwargs):
        self.send_valid_revocation_list = True
        self.resp = None

    def request(self, method, path, **kwargs):
        """Fakes out several http responses.

        Support the following requests:

        - Create admin token ('POST /testadmin/v2.0/tokens')
        - Get versions ('GET /testadmin/')
        - Get v2 user token responses (see fake_v2_responses)

        """
        FakeHTTPConnection.last_requested_url = path
        if method == 'POST' and path == '/testadmin/v2.0/tokens':
            status, body = self.fake_v2_admin_token(path)
        else:
            if path == '/testadmin/':
                # It's a GET versions call
                status = 300
                body = jsonutils.dumps(VERSION_LIST_v2)
            else:
                status, body = self.fake_v2_responses(path)

        self.resp = FakeHTTPResponse(status, body)

    def getresponse(self):
        # If self.resp is set then this is just the response to
        # the earlier request.  If it is not set, then we expect
        # a stack of responses to have been pre-prepared
        if self.resp:
            return self.resp
        else:
            if len(FAKE_RESPONSE_STACK):
                return FAKE_RESPONSE_STACK.pop()
            return FakeHTTPResponse(
                500, jsonutils.dumps('UNEXPECTED RESPONSE'))

    def close(self):
        pass


class v3FakeHTTPConnection(FakeHTTPConnection):
    """Emulate a fake Keystone v3 server."""

    def request(self, method, path, **kwargs):
        """Fakes out several http responses.

        Support the following requests:

        - Create admin token ('POST /testadmin/v2.0/tokens')
        - Get versions ('GET /testadmin/')
        - Get v2 user token responses (see fake_v2_responses)
        - Get v3 user token responses (see fake_v3_responses)

        """
        v3FakeHTTPConnection.last_requested_url = path
        if method == 'POST' and path == '/testadmin/v2.0/tokens':
            status, body = self.fake_v2_admin_token(path)
        else:
            if path == '/testadmin/':
                # It's a GET versions call
                status = 300
                body = jsonutils.dumps(VERSION_LIST_v3)
            elif path.split('/')[2] == 'v2.0':
                status, body = self.fake_v2_responses(path)
            else:
                status, body = self.fake_v3_responses(path, **kwargs)

        self.resp = FakeHTTPResponse(status, body)


class RaisingHTTPConnection(FakeHTTPConnection):
    """An HTTPConnection that always raises."""

    def request(self, method, path, **kwargs):
        raise AssertionError("HTTP request was called.")


class FakeApp(object):
    """This represents a WSGI app protected by the auth_token middleware."""
    def __init__(self, expected_env=None):
        expected_env = expected_env or {}
        self.expected_env = dict(EXPECTED_V2_DEFAULT_ENV_RESPONSE)
        self.expected_env.update(expected_env)

    def __call__(self, env, start_response):
        for k, v in self.expected_env.items():
            assert env[k] == v, '%s != %s' % (env[k], v)

        resp = webob.Response()
        resp.body = 'SUCCESS'
        return resp(env, start_response)


class v3FakeApp(object):
    """This represents a v3 WSGI app protected by the auth_token middleware."""
    def __init__(self, expected_env=None):
        expected_env = expected_env or {}
        # We should always get back the same v2 items
        self.expected_env = dict(EXPECTED_V2_DEFAULT_ENV_RESPONSE)
        # ...and with v3 additions, these are for the DEFAULT TOKEN
        v3_default_env_additions = {
            'HTTP_X_PROJECT_ID': 'tenant_id1',
            'HTTP_X_PROJECT_NAME': 'tenant_name1',
            'HTTP_X_PROJECT_DOMAIN_ID': 'domain_id1',
            'HTTP_X_PROJECT_DOMAIN_NAME': 'domain_name1',
            'HTTP_X_USER_DOMAIN_ID': 'domain_id1',
            'HTTP_X_USER_DOMAIN_NAME': 'domain_name1'
        }
        self.expected_env.update(v3_default_env_additions)
        # And finally update for anything passed in
        self.expected_env.update(expected_env)

    def __call__(self, env, start_response):
        for k, v in self.expected_env.items():
            assert env[k] == v, '%s != %s' % (env[k], v)
        resp = webob.Response()
        resp.body = 'SUCCESS'
        return resp(env, start_response)


class BaseAuthTokenMiddlewareTest(testtools.TestCase):
    """Base test class for auth_token middleware.

    All the tests allow for running with auth_token
    configured for receiving v2 or v3 tokens, with the
    choice being made by passing configuration data into
    Setup().

    The base class will, by default, run all the tests
    expecting v2 token formats.  Child classes can override
    this to specify, for instance, v3 format.

    """
    def setUp(self, expected_env=None, auth_version=None,
              fake_app=None, fake_http=None, token_dict=None):
        testtools.TestCase.setUp(self)
        expected_env = expected_env or {}

        if token_dict:
            self.token_dict = token_dict
        else:
            self.token_dict = {
                'uuid_token_default': UUID_TOKEN_DEFAULT,
                'uuid_token_unscoped': UUID_TOKEN_UNSCOPED,
                'signed_token_scoped': SIGNED_TOKEN_SCOPED,
                'signed_token_scoped_expired': SIGNED_TOKEN_SCOPED_EXPIRED,
                'revoked_token': REVOKED_TOKEN,
                'revoked_token_hash': REVOKED_TOKEN_HASH
            }

        self.conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'signing_dir': CERTDIR,
            'auth_version': auth_version
        }

        # Base assumes v2 for fake app and http, can be overridden for
        # child classes by called set_middleware() directly
        self.fake_app = fake_app or FakeApp
        self.fake_http = fake_http or FakeHTTPConnection
        self.set_middleware(self.fake_app, self.fake_http,
                            expected_env, self.conf)

        self.response_status = None
        self.response_headers = None

        signed_list = 'SIGNED_REVOCATION_LIST'
        valid_signed_list = 'VALID_SIGNED_REVOCATION_LIST'
        globals()[signed_list] = globals()[valid_signed_list]

    def set_fake_http(self, http_handler):
        """Configure the http handler for the auth_token middleware.

        Allows tests to override the default handler on specific tests,
        e.g. to use v2 for those parts of auth_token that still use v2
        tokens while running the v3 test class, i.e. getting an admin
        token or revocation list.

        """
        self.middleware.http_client_class = http_handler

    def set_middleware(self, fake_app=None, fake_http=None,
                       expected_env=None, conf=None):
        """Configure the class ready to call the auth_token middleware.

        Set up the various fake items needed to run the middleware.
        Individual tests that need to further refine these can call this
        function to override the class defaults.

        """
        conf = conf or self.conf
        if fake_http:
            conf['http_handler'] = fake_http
        fake_app = fake_app or self.fake_app
        self.middleware = auth_token.AuthProtocol(fake_app(expected_env), conf)
        self.middleware._iso8601 = iso8601
        self.middleware.revoked_file_name = tempfile.mkstemp()[1]
        self.middleware.token_revocation_list = jsonutils.dumps(
            {"revoked": [], "extra": "success"})

    def tearDown(self):
        testtools.TestCase.tearDown(self)
        try:
            os.remove(self.middleware.revoked_file_name)
        except OSError:
            pass

    def start_fake_response(self, status, headers):
        self.response_status = int(status.split(' ', 1)[0])
        self.response_headers = dict(headers)


if tuple(sys.version_info)[0:2] < (2, 7):

    # 2.6 doesn't have the assert dict equals so make sure that it exists
    class AdjustedBaseAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest):
        def assertIsInstance(self, obj, cls, msg=None):
            """Same as self.assertTrue(isinstance(obj, cls)), with a nicer
            default message.
            """
            if not isinstance(obj, cls):
                standardMsg = '%s is not an instance of %r' % (obj, cls)
                self.fail(self._formatMessage(msg, standardMsg))

        def assertDictEqual(self, d1, d2, msg=None):
            # Simple version taken from 2.7
            self.assertIsInstance(d1, dict,
                                  'First argument is not a dictionary')
            self.assertIsInstance(d2, dict,
                                  'Second argument is not a dictionary')
            if d1 != d2:
                if msg:
                    self.fail(msg)
                else:
                    standardMsg = '%r != %r' % (d1, d2)
                    self.fail(standardMsg)

    BaseAuthTokenMiddlewareTest = AdjustedBaseAuthTokenMiddlewareTest


class StackResponseAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest):
    """Auth Token middleware test setup that allows the tests to define
    a stack of responses to HTTP requests in the test and get those
    responses back in sequence for testing.

    Example::

        resp1 = FakeHTTPResponse(401, jsonutils.dumps(''))
        resp2 = FakeHTTPResponse(200, jsonutils.dumps({
            'access': {
                'token': {'id': 'admin_token2'},
            },
            })
        FAKE_RESPONSE_STACK.append(resp1)
        FAKE_RESPONSE_STACK.append(resp2)

        ... do your testing code here ...

    """

    def setUp(self):
        super(StackResponseAuthTokenMiddlewareTest, self).setUp()

    def test_fetch_revocation_list_with_expire(self):
        # first response to revocation list should return 401 Unauthorized
        # to pretend to be an expired token
        resp1 = FakeHTTPResponse(200, jsonutils.dumps({
            'access': {
                'token': {'id': 'admin_token2'},
            },
        }))
        resp2 = FakeHTTPResponse(401, jsonutils.dumps(''))
        resp3 = FakeHTTPResponse(200, jsonutils.dumps({
            'access': {
                'token': {'id': 'admin_token2'},
            },
        }))
        resp4 = FakeHTTPResponse(200, SIGNED_REVOCATION_LIST)

        # first get_admin_token() call
        FAKE_RESPONSE_STACK.append(resp1)
        # request revocation list, get "unauthorized" due to simulated expired
        # token
        FAKE_RESPONSE_STACK.append(resp2)
        # request a new admin_token
        FAKE_RESPONSE_STACK.append(resp3)
        # request revocation list, get the revocation list properly
        FAKE_RESPONSE_STACK.append(resp4)

        fetched_list = jsonutils.loads(self.middleware.fetch_revocation_list())
        self.assertEqual(fetched_list, REVOCATION_LIST)


class DiabloAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest):
    """Auth Token middleware should understand Diablo keystone responses."""
    def setUp(self):
        # pre-diablo only had Tenant ID, which was also the Name
        expected_env = {
            'HTTP_X_TENANT_ID': 'tenant_id1',
            'HTTP_X_TENANT_NAME': 'tenant_id1',
            # now deprecated (diablo-compat)
            'HTTP_X_TENANT': 'tenant_id1',
        }
        super(DiabloAuthTokenMiddlewareTest, self).setUp(
            expected_env=expected_env)

    def test_valid_diablo_response(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = VALID_DIABLO_TOKEN
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertTrue('keystone.token_info' in req.environ)


class NoMemcacheAuthToken(BaseAuthTokenMiddlewareTest):

    def setUp(self):
        super(NoMemcacheAuthToken, self).setUp()
        self.useFixture(DisableModuleFixture('memcache'))

    def test_nomemcache(self):
        conf = {
            'admin_token': 'admin_token1',
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'memcached_servers': 'localhost:11211',
        }

        auth_token.AuthProtocol(FakeApp(), conf)

    def test_not_use_cache_from_env(self):
        env = {'swift.cache': 'CACHE_TEST'}
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': 'localhost:11211'
        }
        self.set_middleware(conf=conf)
        self.middleware._init_cache(env)
        self.assertNotEqual(self.middleware._cache, 'CACHE_TEST')


class AuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest):

    def test_init_does_not_call_http(self):
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'revocation_cache_time': 1
        }
        self.set_fake_http(RaisingHTTPConnection)
        self.set_middleware(conf=conf, fake_http=RaisingHTTPConnection)

    def assert_valid_last_url(self, token_id):
        # Default version (v2) has id in the token, override this
        # method for v3 and other versions
        self.assertEqual("/testadmin/v2.0/tokens/%s" % token_id,
                         self.middleware.http_client_class.last_requested_url)

    def assert_valid_request_200(self, token, with_catalog=True):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        if with_catalog:
            self.assertTrue(req.headers.get('X-Service-Catalog'))
        self.assertEqual(body, ['SUCCESS'])
        self.assertTrue('keystone.token_info' in req.environ)

    def test_valid_uuid_request(self):
        self.assert_valid_request_200(self.token_dict['uuid_token_default'])
        self.assert_valid_last_url(self.token_dict['uuid_token_default'])

    def test_valid_signed_request(self):
        self.middleware.http_client_class.last_requested_url = ''
        self.assert_valid_request_200(
            self.token_dict['signed_token_scoped'])
        self.assertEqual(self.middleware.conf['auth_admin_prefix'],
                         "/testadmin")
        #ensure that signed requests do not generate HTTP traffic
        self.assertEqual(
            '', self.middleware.http_client_class.last_requested_url)

    def test_revoked_token_receives_401(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.token_dict['revoked_token']
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)

    def get_revocation_list_json(self, token_ids=None):
        if token_ids is None:
            token_ids = [self.token_dict['revoked_token_hash']]
        revocation_list = {'revoked': [{'id': x, 'expires': timeutils.utcnow()}
                                       for x in token_ids]}
        return jsonutils.dumps(revocation_list)

    def test_is_signed_token_revoked_returns_false(self):
        #explicitly setting an empty revocation list here to document intent
        self.middleware.token_revocation_list = jsonutils.dumps(
            {"revoked": [], "extra": "success"})
        result = self.middleware.is_signed_token_revoked(
            self.token_dict['revoked_token'])
        self.assertFalse(result)

    def test_is_signed_token_revoked_returns_true(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        result = self.middleware.is_signed_token_revoked(
            self.token_dict['revoked_token'])
        self.assertTrue(result)

    def test_verify_signed_token_raises_exception_for_revoked_token(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        self.assertRaises(auth_token.InvalidUserToken,
                          self.middleware.verify_signed_token,
                          self.token_dict['revoked_token'])

    def test_verify_signed_token_succeeds_for_unrevoked_token(self):
        self.middleware.token_revocation_list = self.get_revocation_list_json()
        self.middleware.verify_signed_token(
            self.token_dict['signed_token_scoped'])

    def test_cert_file_missing(self):
        self.assertFalse(self.middleware.cert_file_missing(
                         "openstack: /tmp/haystack: No such file or directory",
                         "/tmp/needle"))
        self.assertTrue(self.middleware.cert_file_missing(
                        "openstack: /not/exist: No such file or directory",
                        "/not/exist"))

    def test_get_token_revocation_list_fetched_time_returns_min(self):
        self.middleware.token_revocation_list_fetched_time = None
        self.middleware.revoked_file_name = ''
        self.assertEqual(self.middleware.token_revocation_list_fetched_time,
                         datetime.datetime.min)

    def test_get_token_revocation_list_fetched_time_returns_mtime(self):
        self.middleware.token_revocation_list_fetched_time = None
        mtime = os.path.getmtime(self.middleware.revoked_file_name)
        fetched_time = datetime.datetime.fromtimestamp(mtime)
        self.assertEqual(self.middleware.token_revocation_list_fetched_time,
                         fetched_time)

    def test_get_token_revocation_list_fetched_time_returns_value(self):
        expected = self.middleware._token_revocation_list_fetched_time
        self.assertEqual(self.middleware.token_revocation_list_fetched_time,
                         expected)

    def test_get_revocation_list_returns_fetched_list(self):
        # auth_token uses v2 to fetch this, so don't allow the v3
        # tests to override the fake http connection
        self.set_fake_http(FakeHTTPConnection)
        self.middleware.token_revocation_list_fetched_time = None
        os.remove(self.middleware.revoked_file_name)
        self.assertEqual(self.middleware.token_revocation_list,
                         REVOCATION_LIST)

    def test_get_revocation_list_returns_current_list_from_memory(self):
        self.assertEqual(self.middleware.token_revocation_list,
                         self.middleware._token_revocation_list)

    def test_get_revocation_list_returns_current_list_from_disk(self):
        in_memory_list = self.middleware.token_revocation_list
        self.middleware._token_revocation_list = None
        self.assertEqual(self.middleware.token_revocation_list, in_memory_list)

    def test_invalid_revocation_list_raises_service_error(self):
        globals()['SIGNED_REVOCATION_LIST'] = "{}"
        self.assertRaises(auth_token.ServiceError,
                          self.middleware.fetch_revocation_list)

    def test_fetch_revocation_list(self):
        # auth_token uses v2 to fetch this, so don't allow the v3
        # tests to override the fake http connection
        self.set_fake_http(FakeHTTPConnection)
        fetched_list = jsonutils.loads(self.middleware.fetch_revocation_list())
        self.assertEqual(fetched_list, REVOCATION_LIST)

    def test_request_invalid_uuid_token(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = 'invalid-token'
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_request_invalid_signed_token(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = INVALID_SIGNED_TOKEN
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_request_no_token(self):
        req = webob.Request.blank('/')
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_request_no_token_log_message(self):
        class FakeLog(object):
            def __init__(self):
                self.msg = None
                self.debugmsg = None

            def warn(self, msg=None, *args, **kwargs):
                self.msg = msg

            def debug(self, msg=None, *args, **kwargs):
                self.debugmsg = msg

        self.middleware.LOG = FakeLog()
        self.middleware.delay_auth_decision = False
        self.assertRaises(auth_token.InvalidUserToken,
                          self.middleware._get_user_token_from_header, {})
        self.assertIsNotNone(self.middleware.LOG.msg)
        self.assertIsNotNone(self.middleware.LOG.debugmsg)

    def test_request_no_token_http(self):
        req = webob.Request.blank('/', environ={'REQUEST_METHOD': 'HEAD'})
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_protocol': 'http',
            'auth_admin_prefix': '/testadmin',
        }
        self.set_middleware(conf=conf)
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='http://keystone.example.com:1234'")
        self.assertEqual(body, [''])

    def test_request_blank_token(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = ''
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def _get_cached_token(self, token):
        token_id = cms.cms_hash_token(token)
        # NOTE(vish): example tokens are expired so skip the expiration check.
        return self.middleware._cache_get(token_id, ignore_expires=True)

    def test_memcache(self):
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped']
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertNotEqual(self._get_cached_token(token), None)

    def test_expired(self):
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped_expired']
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)

    def test_memcache_set_invalid(self):
        req = webob.Request.blank('/')
        token = 'invalid-token'
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertRaises(auth_token.InvalidUserToken,
                          self._get_cached_token, token)

    def test_memcache_set_expired(self, extra_conf={}, extra_environ={}):
        token_cache_time = 10
        conf = {
            'token_cache_time': token_cache_time,
            'signing_dir': CERTDIR,
        }
        conf.update(extra_conf)
        self.set_middleware(conf=conf)
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped']
        req.headers['X-Auth-Token'] = token
        req.environ.update(extra_environ)
        try:
            now = datetime.datetime.utcnow()
            timeutils.set_time_override(now)
            self.middleware(req.environ, self.start_fake_response)
            self.assertNotEqual(self._get_cached_token(token), None)
            expired = now + datetime.timedelta(seconds=token_cache_time)
            timeutils.set_time_override(expired)
            self.assertEqual(self._get_cached_token(token), None)
        finally:
            timeutils.clear_time_override()

    def test_old_swift_memcache_set_expired(self):
        extra_conf = {'cache': 'swift.cache'}
        extra_environ = {'swift.cache': FakeSwiftOldMemcacheClient()}
        self.test_memcache_set_expired(extra_conf, extra_environ)

    def test_swift_memcache_set_expired(self):
        extra_conf = {'cache': 'swift.cache'}
        extra_environ = {'swift.cache': memorycache.Client()}
        self.test_memcache_set_expired(extra_conf, extra_environ)

    def test_use_cache_from_env(self):
        env = {'swift.cache': 'CACHE_TEST'}
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'cache': 'swift.cache',
            'memcached_servers': ['localhost:11211']
        }
        self.set_middleware(conf=conf)
        self.middleware._init_cache(env)
        self.assertEqual(self.middleware._cache, 'CACHE_TEST')

    def test_will_expire_soon(self):
        tenseconds = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=10)
        self.assertTrue(auth_token.will_expire_soon(tenseconds))
        fortyseconds = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=40)
        self.assertFalse(auth_token.will_expire_soon(fortyseconds))

    def test_encrypt_cache_data(self):
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'encrypt',
            'memcache_secret_key': 'mysecret'
        }
        self.set_middleware(conf=conf)
        token = 'my_token'
        data = ('this_data', 10e100)
        self.middleware._init_cache({})
        self.middleware._cache_store(token, data)
        self.assertEqual(self.middleware._cache_get(token), data[0])

    def test_sign_cache_data(self):
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'mac',
            'memcache_secret_key': 'mysecret'
        }
        self.set_middleware(conf=conf)
        token = 'my_token'
        data = ('this_data', 10e100)
        self.middleware._init_cache({})
        self.middleware._cache_store(token, data)
        self.assertEqual(self.middleware._cache_get(token), data[0])

    def test_no_memcache_protection(self):
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': ['localhost:11211'],
            'memcache_secret_key': 'mysecret'
        }
        self.set_middleware(conf=conf)
        token = 'my_token'
        data = ('this_data', 10e100)
        self.middleware._init_cache({})
        self.middleware._cache_store(token, data)
        self.assertEqual(self.middleware._cache_get(token), data[0])

    def test_assert_valid_memcache_protection_config(self):
        # test missing memcache_secret_key
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'Encrypt'
        }
        self.assertRaises(Exception, self.set_middleware, conf)
        # test invalue memcache_security_strategy
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'whatever'
        }
        self.assertRaises(Exception, self.set_middleware, conf)
        # test missing memcache_secret_key
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'mac'
        }
        self.assertRaises(Exception, self.set_middleware, conf)
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'Encrypt',
            'memcache_secret_key': ''
        }
        self.assertRaises(Exception, self.set_middleware, conf)
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'mAc',
            'memcache_secret_key': ''
        }
        self.assertRaises(Exception, self.set_middleware, conf)

    def test_config_revocation_cache_timeout(self):
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'revocation_cache_time': 24
        }
        middleware = auth_token.AuthProtocol(self.fake_app, conf)
        self.assertEquals(middleware.token_revocation_list_cache_timeout,
                          datetime.timedelta(seconds=24))


class CertDownloadMiddlewareTest(BaseAuthTokenMiddlewareTest):
    def setUp(self):
        super(CertDownloadMiddlewareTest, self).setUp()
        self.base_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.base_dir)
        super(CertDownloadMiddlewareTest, self).tearDown()

    # Usually we supply a signed_dir with pre-installed certificates,
    # so invocation of /usr/bin/openssl succeeds. This time we give it
    # an empty directory, so it fails.
    def test_request_no_token_dummy(self):
        cert_dir = os.path.join(self.base_dir, 'certs')
        os.mkdir(cert_dir)
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_protocol': 'http',
            'auth_admin_prefix': '/testadmin',
            'signing_dir': cert_dir,
        }
        self.set_middleware(fake_http=self.fake_http, conf=conf)
        self.assertRaises(cms.subprocess.CalledProcessError,
                          self.middleware.verify_signed_token,
                          self.token_dict['signed_token_scoped'])


class v2AuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest):
    """v2 token specific tests.

    There are some differences between how the auth-token middleware handles
    v2 and v3 tokens over and above the token formats, namely:

    - A v3 keystone server will auto scope a token to a user's default project
      if no scope is specified. A v2 server assumes that the auth-token
      middleware will do that.
    - A v2 keystone server may issue a token without a catalog, even with a
      tenant

    The tests below were originally part of the generic AuthTokenMiddlewareTest
    class, but now, since they really are v2 specifc, they are included here.

    """
    def assert_unscoped_default_tenant_auto_scopes(self, token):
        """Unscoped v2 requests with a default tenant should "auto-scope."

        The implied scope is the user's tenant ID.

        """
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertEqual(body, ['SUCCESS'])
        self.assertTrue('keystone.token_info' in req.environ)

    def test_default_tenant_uuid_token(self):
        self.assert_unscoped_default_tenant_auto_scopes(UUID_TOKEN_DEFAULT)

    def test_default_tenant_signed_token(self):
        self.assert_unscoped_default_tenant_auto_scopes(SIGNED_TOKEN_SCOPED)

    def assert_unscoped_token_receives_401(self, token):
        """Unscoped requests with no default tenant ID should be rejected."""
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_unscoped_uuid_token_receives_401(self):
        self.assert_unscoped_token_receives_401(UUID_TOKEN_UNSCOPED)

    def test_unscoped_pki_token_receives_401(self):
        self.assert_unscoped_token_receives_401(SIGNED_TOKEN_UNSCOPED)

    def test_request_prevent_service_catalog_injection(self):
        req = webob.Request.blank('/')
        req.headers['X-Service-Catalog'] = '[]'
        req.headers['X-Auth-Token'] = UUID_TOKEN_NO_SERVICE_CATALOG
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertFalse(req.headers.get('X-Service-Catalog'))
        self.assertEqual(body, ['SUCCESS'])

    def test_valid_uuid_request_forced_to_2_0(self):
        """Test forcing auth_token to use lower api version.

        By installing the v3 http hander, auth_token will be get
        a version list that looks like a v3 server - from which it
        would normally chose v3.0 as the auth version.  However, here
        we specify v2.0 in the configuration - which should force
        auth_token to use that version instead.

        """
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'signing_dir': CERTDIR,
            'auth_version': 'v2.0'
        }
        self.set_middleware(fake_http=v3FakeHTTPConnection, conf=conf)
        # This tests will only work is auth_token has chosen to use the
        # lower, v2, api version
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = UUID_TOKEN_DEFAULT
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertEqual("/testadmin/v2.0/tokens/%s" % UUID_TOKEN_DEFAULT,
                         v3FakeHTTPConnection.last_requested_url)

    def test_invalid_auth_version_request(self):
        conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_admin_prefix': '/testadmin',
            'signing_dir': CERTDIR,
            'auth_version': 'v1.0'      # v1.0 is no longer supported
        }
        self.assertRaises(Exception, self.set_middleware, conf)


class v3AuthTokenMiddlewareTest(AuthTokenMiddlewareTest):
    """Test auth_token middleware with v3 tokens.

    Re-execute the AuthTokenMiddlewareTest class tests, but with the
    the auth_token middleware configured to expect v3 tokens back from
    a keystone server.

    This is done by configuring the AuthTokenMiddlewareTest class via
    its Setup(), passing in v3 style data that will then be used by
    the tests themselves.  This approach has been used to ensure we
    really are running the same tests for both v2 and v3 tokens.

    There a few additional specific test for v3 only:

    - We allow an unscoped token to be validated (as unscoped), where
      as for v2 tokens, the auth_token middleware is expected to try and
      auto-scope it (and fail if there is no default tenant)
    - Domain scoped tokens

    Since we don't specify an auth version for auth_token to use, by
    definition we are thefore implicitely testing that it will use
    the highest available auth version, i.e. v3.0

    """
    def setUp(self):
        token_dict = {
            'uuid_token_default': v3_UUID_TOKEN_DEFAULT,
            'uuid_token_unscoped': v3_UUID_TOKEN_UNSCOPED,
            'signed_token_scoped': SIGNED_v3_TOKEN_SCOPED,
            'signed_token_scoped_expired': SIGNED_TOKEN_SCOPED_EXPIRED,
            'revoked_token': REVOKED_v3_TOKEN,
            'revoked_token_hash': REVOKED_v3_TOKEN_HASH
        }
        super(v3AuthTokenMiddlewareTest, self).setUp(
            auth_version='v3.0',
            fake_app=v3FakeApp,
            fake_http=v3FakeHTTPConnection,
            token_dict=token_dict)

    def assert_valid_last_url(self, token_id):
        # Token ID is not part of the url in v3, so override
        # this assert test in the base class
        self.assertEqual('/testadmin/v3/auth/tokens',
                         v3FakeHTTPConnection.last_requested_url)

    def test_valid_unscoped_uuid_request(self):
        # Remove items that won't be in an unscoped token
        delta_expected_env = {
            'HTTP_X_PROJECT_ID': None,
            'HTTP_X_PROJECT_NAME': None,
            'HTTP_X_PROJECT_DOMAIN_ID': None,
            'HTTP_X_PROJECT_DOMAIN_NAME': None,
            'HTTP_X_TENANT_ID': None,
            'HTTP_X_TENANT_NAME': None,
            'HTTP_X_ROLES': '',
            'HTTP_X_TENANT': None,
            'HTTP_X_ROLE': '',
        }
        self.set_middleware(expected_env=delta_expected_env)
        self.assert_valid_request_200(v3_UUID_TOKEN_UNSCOPED,
                                      with_catalog=False)
        self.assertEqual('/testadmin/v3/auth/tokens',
                         v3FakeHTTPConnection.last_requested_url)

    def test_domain_scoped_uuid_request(self):
        # Modify items compared to default token for a domain scope
        delta_expected_env = {
            'HTTP_X_DOMAIN_ID': 'domain_id1',
            'HTTP_X_DOMAIN_NAME': 'domain_name1',
            'HTTP_X_PROJECT_ID': None,
            'HTTP_X_PROJECT_NAME': None,
            'HTTP_X_PROJECT_DOMAIN_ID': None,
            'HTTP_X_PROJECT_DOMAIN_NAME': None,
            'HTTP_X_TENANT_ID': None,
            'HTTP_X_TENANT_NAME': None,
            'HTTP_X_TENANT': None
        }
        self.set_middleware(expected_env=delta_expected_env)
        self.assert_valid_request_200(v3_UUID_TOKEN_DOMAIN_SCOPED)
        self.assertEqual('/testadmin/v3/auth/tokens',
                         v3FakeHTTPConnection.last_requested_url)


class TokenEncodingTest(testtools.TestCase):
    def test_unquoted_token(self):
        self.assertEqual('foo%20bar', auth_token.safe_quote('foo bar'))

    def test_quoted_token(self):
        self.assertEqual('foo%20bar', auth_token.safe_quote('foo%20bar'))
