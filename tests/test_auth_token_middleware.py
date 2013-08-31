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
import stat
import sys
import tempfile
import testtools
import uuid

import fixtures
import httpretty
import mock
import webob

from keystoneclient.common import cms
from keystoneclient.middleware import auth_token
from keystoneclient.openstack.common import jsonutils
from keystoneclient.openstack.common import memorycache
from keystoneclient.openstack.common import timeutils

import client_fixtures

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


BASE_HOST = 'https://keystone.example.com:1234'
BASE_URI = '%s/testadmin' % BASE_HOST
FAKE_ADMIN_TOKEN_ID = 'admin_token2'
FAKE_ADMIN_TOKEN = jsonutils.dumps(
    {'access': {'token': {'id': FAKE_ADMIN_TOKEN_ID,
                          'expires': '2022-10-03T16:58:01Z'}}})


VERSION_LIST_v3 = jsonutils.dumps({
    "versions": {
        "values": [
            {
                "id": "v3.0",
                "status": "stable",
                "updated": "2013-03-06T00:00:00Z",
                "links": [{'href': '%s/v3' % BASE_URI, 'rel': 'self'}]
            },
            {
                "id": "v2.0",
                "status": "stable",
                "updated": "2011-11-19T00:00:00Z",
                "links": [{'href': '%s/v2.0' % BASE_URI, 'rel': 'self'}]
            }
        ]
    }
})

VERSION_LIST_v2 = jsonutils.dumps({
    "versions": {
        "values": [
            {
                "id": "v2.0",
                "status": "stable",
                "updated": "2011-11-19T00:00:00Z",
                "links": []
            }
        ]
    }
})

ERROR_TOKEN = '7ae290c2a06244c4b41692eb4e9225f2'


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


class FakeApp(object):
    """This represents a WSGI app protected by the auth_token middleware."""

    def __init__(self, expected_env=None):
        self.expected_env = dict(EXPECTED_V2_DEFAULT_ENV_RESPONSE)

        if expected_env:
            self.expected_env.update(expected_env)

    def __call__(self, env, start_response):
        for k, v in self.expected_env.items():
            assert env[k] == v, '%s != %s' % (env[k], v)

        resp = webob.Response()
        resp.body = 'SUCCESS'
        return resp(env, start_response)


class v3FakeApp(FakeApp):
    """This represents a v3 WSGI app protected by the auth_token middleware."""

    def __init__(self, expected_env=None):

        # with v3 additions, these are for the DEFAULT TOKEN
        v3_default_env_additions = {
            'HTTP_X_PROJECT_ID': 'tenant_id1',
            'HTTP_X_PROJECT_NAME': 'tenant_name1',
            'HTTP_X_PROJECT_DOMAIN_ID': 'domain_id1',
            'HTTP_X_PROJECT_DOMAIN_NAME': 'domain_name1',
            'HTTP_X_USER_DOMAIN_ID': 'domain_id1',
            'HTTP_X_USER_DOMAIN_NAME': 'domain_name1'
        }

        if expected_env:
            v3_default_env_additions.update(expected_env)

        super(v3FakeApp, self).__init__(v3_default_env_additions)


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
    def setUp(self, expected_env=None, auth_version=None, fake_app=None):
        testtools.TestCase.setUp(self)

        self.expected_env = expected_env or dict()
        self.fake_app = fake_app or FakeApp
        self.middleware = None

        self.conf = {
            'auth_host': 'keystone.example.com',
            'auth_port': 1234,
            'auth_protocol': 'https',
            'auth_admin_prefix': '/testadmin',
            'signing_dir': client_fixtures.CERTDIR,
            'auth_version': auth_version
        }

        self.response_status = None
        self.response_headers = None

    def set_middleware(self, fake_app=None, expected_env=None, conf=None):
        """Configure the class ready to call the auth_token middleware.

        Set up the various fake items needed to run the middleware.
        Individual tests that need to further refine these can call this
        function to override the class defaults.

        """
        if conf:
            self.conf.update(conf)

        if not fake_app:
            fake_app = self.fake_app

        if expected_env:
            self.expected_env.update(expected_env)

        self.middleware = auth_token.AuthProtocol(fake_app(self.expected_env),
                                                  self.conf)
        self.middleware._iso8601 = iso8601
        self.middleware.revoked_file_name = tempfile.mkstemp()[1]
        self.middleware.token_revocation_list = jsonutils.dumps(
            {"revoked": [], "extra": "success"})

    def tearDown(self):
        testtools.TestCase.tearDown(self)
        if self.middleware:
            try:
                os.remove(self.middleware.revoked_file_name)
            except OSError:
                pass

    def start_fake_response(self, status, headers):
        self.response_status = int(status.split(' ', 1)[0])
        self.response_headers = dict(headers)

    def assertLastPath(self, path):
        if path:
            self.assertEqual(path, httpretty.httpretty.last_request.path)
        else:
            self.assertIsInstance(httpretty.httpretty.last_request,
                                  httpretty.core.HTTPrettyRequestEmpty)

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


class MultiStepAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest):

    @httpretty.activate
    def test_fetch_revocation_list_with_expire(self):
        self.set_middleware()

        # Get a token, then try to retrieve revocation list and get a 401.
        # Get a new token, try to retrieve revocation list and return 200.
        httpretty.register_uri(httpretty.POST, "%s/v2.0/tokens" % BASE_URI,
                               body=FAKE_ADMIN_TOKEN)

        responses = [httpretty.Response(body='', status=401),
                     httpretty.Response(
                         body=client_fixtures.SIGNED_REVOCATION_LIST)]

        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/tokens/revoked" % BASE_URI,
                               responses=responses)

        fetched_list = jsonutils.loads(self.middleware.fetch_revocation_list())
        self.assertEqual(fetched_list, client_fixtures.REVOCATION_LIST)

        # Check that 4 requests have been made
        self.assertEqual(len(httpretty.httpretty.latest_requests), 4)


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

        httpretty.httpretty.reset()
        httpretty.enable()

        httpretty.register_uri(httpretty.GET,
                               "%s/" % BASE_URI,
                               body=VERSION_LIST_v2,
                               status=300)

        httpretty.register_uri(httpretty.POST,
                               "%s/v2.0/tokens" % BASE_URI,
                               body=FAKE_ADMIN_TOKEN)

        self.token_id = client_fixtures.VALID_DIABLO_TOKEN
        token_response = client_fixtures.JSON_TOKEN_RESPONSES[self.token_id]

        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/tokens/%s" % (BASE_URI, self.token_id),
                               body=token_response)

        self.set_middleware()

    def tearDown(self):
        httpretty.disable()
        super(DiabloAuthTokenMiddlewareTest, self).tearDown()

    def test_valid_diablo_response(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = self.token_id
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
            'memcached_servers': 'localhost:11211'
        }
        self.set_middleware(conf=conf)
        self.middleware._init_cache(env)
        self.assertNotEqual(self.middleware._cache, 'CACHE_TEST')


class CommonAuthTokenMiddlewareTest(object):

    def test_init_does_not_call_http(self):
        conf = {
            'revocation_cache_time': 1
        }
        self.set_middleware(conf=conf)
        self.assertLastPath(None)

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
        self.assert_valid_request_200(
            self.token_dict['signed_token_scoped'])
        self.assertEqual(self.middleware.conf['auth_admin_prefix'],
                         "/testadmin")
        #ensure that signed requests do not generate HTTP traffic
        self.assertLastPath(None)

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

    def test_verify_signing_dir_create_while_missing(self):
        tmp_name = uuid.uuid4().hex
        test_parent_signing_dir = "/tmp/%s" % tmp_name
        self.middleware.signing_dirname = "/tmp/%s/%s" % ((tmp_name,) * 2)
        self.middleware.signing_cert_file_name = "%s/test.pem" %\
            self.middleware.signing_dirname
        self.middleware.verify_signing_dir()
        # NOTE(wu_wenxiang): Verify if the signing dir was created as expected.
        self.assertTrue(os.path.isdir(self.middleware.signing_dirname))
        self.assertTrue(os.access(self.middleware.signing_dirname, os.W_OK))
        self.assertEqual(os.stat(self.middleware.signing_dirname).st_uid,
                         os.getuid())
        self.assertEqual(
            stat.S_IMODE(os.stat(self.middleware.signing_dirname).st_mode),
            stat.S_IRWXU)
        shutil.rmtree(test_parent_signing_dir)

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
        self.middleware.token_revocation_list_fetched_time = None
        os.remove(self.middleware.revoked_file_name)
        self.assertEqual(self.middleware.token_revocation_list,
                         client_fixtures.REVOCATION_LIST)

    def test_get_revocation_list_returns_current_list_from_memory(self):
        self.assertEqual(self.middleware.token_revocation_list,
                         self.middleware._token_revocation_list)

    def test_get_revocation_list_returns_current_list_from_disk(self):
        in_memory_list = self.middleware.token_revocation_list
        self.middleware._token_revocation_list = None
        self.assertEqual(self.middleware.token_revocation_list, in_memory_list)

    def test_invalid_revocation_list_raises_service_error(self):
        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/tokens/revoked" % BASE_URI,
                               body="{}",
                               status=200)

        self.assertRaises(auth_token.ServiceError,
                          self.middleware.fetch_revocation_list)

    def test_fetch_revocation_list(self):
        # auth_token uses v2 to fetch this, so don't allow the v3
        # tests to override the fake http connection
        fetched_list = jsonutils.loads(self.middleware.fetch_revocation_list())
        self.assertEqual(fetched_list, client_fixtures.REVOCATION_LIST)

    def test_request_invalid_uuid_token(self):
        # remember because we are testing the middleware we stub the connection
        # to the keystone server, but this is not what gets returned
        invalid_uri = "%s/v2.0/tokens/invalid-token" % BASE_URI
        httpretty.register_uri(httpretty.GET, invalid_uri, body="", status=404)

        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = 'invalid-token'
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_request_invalid_signed_token(self):
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = client_fixtures.INVALID_SIGNED_TOKEN
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
        self.set_middleware()
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")
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
        # NOTE(jamielennox): it appears that httpretty can mess with the
        # memcache socket. Just disable it as it's not required here anyway.
        httpretty.disable()
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped']
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertNotEqual(self._get_cached_token(token), None)

    def test_expired(self):
        httpretty.disable()
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped_expired']
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)

    def test_memcache_set_invalid_uuid(self):
        invalid_uri = "%s/v2.0/tokens/invalid-token" % BASE_URI
        httpretty.register_uri(httpretty.GET, invalid_uri, body="", status=404)

        req = webob.Request.blank('/')
        token = 'invalid-token'
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertRaises(auth_token.InvalidUserToken,
                          self._get_cached_token, token)

    def test_memcache_set_invalid_signed(self):
        req = webob.Request.blank('/')
        token = self.token_dict['signed_token_scoped_expired']
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertRaises(auth_token.InvalidUserToken,
                          self._get_cached_token, token)

    def test_memcache_set_expired(self, extra_conf={}, extra_environ={}):
        httpretty.disable()
        token_cache_time = 10
        conf = {
            'token_cache_time': token_cache_time,
            'signing_dir': client_fixtures.CERTDIR,
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
        httpretty.disable()
        conf = {
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
        httpretty.disable()
        conf = {
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
        httpretty.disable()
        conf = {
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
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'Encrypt'
        }
        self.assertRaises(Exception, self.set_middleware, conf=conf)
        # test invalue memcache_security_strategy
        conf = {
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'whatever'
        }
        self.assertRaises(Exception, self.set_middleware, conf=conf)
        # test missing memcache_secret_key
        conf = {
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'mac'
        }
        self.assertRaises(Exception, self.set_middleware, conf=conf)
        conf = {
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'Encrypt',
            'memcache_secret_key': ''
        }
        self.assertRaises(Exception, self.set_middleware, conf=conf)
        conf = {
            'memcached_servers': ['localhost:11211'],
            'memcache_security_strategy': 'mAc',
            'memcache_secret_key': ''
        }
        self.assertRaises(Exception, self.set_middleware, conf=conf)

    def test_config_revocation_cache_timeout(self):
        conf = {
            'revocation_cache_time': 24
        }
        middleware = auth_token.AuthProtocol(self.fake_app, conf)
        self.assertEquals(middleware.token_revocation_list_cache_timeout,
                          datetime.timedelta(seconds=24))

    def test_http_error_not_cached_token(self):
        """Test to don't cache token as invalid on network errors.

        We use UUID tokens since they are the easiest one to reach
        get_http_connection.
        """
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = ERROR_TOKEN
        self.middleware.http_request_max_retries = 0
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self._get_cached_token(ERROR_TOKEN), None)
        self.assert_valid_last_url(ERROR_TOKEN)

    def test_http_request_max_retries(self):
        times_retry = 10

        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = ERROR_TOKEN

        conf = {'http_request_max_retries': times_retry}
        self.set_middleware(conf=conf)

        with mock.patch('time.sleep') as mock_obj:
            self.middleware(req.environ, self.start_fake_response)

        self.assertEqual(mock_obj.call_count, times_retry)


class CertDownloadMiddlewareTest(BaseAuthTokenMiddlewareTest):
    def setUp(self):
        super(CertDownloadMiddlewareTest, self).setUp()
        self.base_dir = tempfile.mkdtemp()
        self.cert_dir = os.path.join(self.base_dir, 'certs')
        os.mkdir(self.cert_dir)
        conf = {
            'signing_dir': self.cert_dir,
        }
        self.set_middleware(conf=conf)

        httpretty.enable()

    def tearDown(self):
        httpretty.disable()
        shutil.rmtree(self.base_dir)
        super(CertDownloadMiddlewareTest, self).tearDown()

    # Usually we supply a signed_dir with pre-installed certificates,
    # so invocation of /usr/bin/openssl succeeds. This time we give it
    # an empty directory, so it fails.
    def test_request_no_token_dummy(self):
        cms._ensure_subprocess()

        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/certificates/ca" % BASE_URI,
                               status=404)
        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/certificates/signing" % BASE_URI,
                               status=404)
        self.assertRaises(cms.subprocess.CalledProcessError,
                          self.middleware.verify_signed_token,
                          client_fixtures.SIGNED_TOKEN_SCOPED)

    def test_fetch_signing_cert(self):
        data = 'FAKE CERT'
        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/certificates/signing" % BASE_URI,
                               body=data)
        self.middleware.fetch_signing_cert()

        with open(self.middleware.signing_cert_file_name, 'r') as f:
            self.assertEqual(f.read(), data)

        self.assertEqual("/testadmin/v2.0/certificates/signing",
                         httpretty.httpretty.last_request.path)

    def test_fetch_signing_ca(self):
        data = 'FAKE CA'
        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/certificates/ca" % BASE_URI,
                               body=data)
        self.middleware.fetch_ca_cert()

        with open(self.middleware.ca_file_name, 'r') as f:
            self.assertEqual(f.read(), data)

        self.assertEqual("/testadmin/v2.0/certificates/ca",
                         httpretty.httpretty.last_request.path)

    def test_prefix_trailing_slash(self):
        self.conf['auth_admin_prefix'] = '/newadmin/'

        httpretty.register_uri(httpretty.GET,
                               "%s/newadmin/v2.0/certificates/ca" % BASE_HOST,
                               body='FAKECA')
        httpretty.register_uri(httpretty.GET,
                               "%s/newadmin/v2.0/certificates/signing" %
                               BASE_HOST, body='FAKECERT')

        self.set_middleware(conf=self.conf)

        self.middleware.fetch_ca_cert()

        self.assertEqual('/newadmin/v2.0/certificates/ca',
                         httpretty.httpretty.last_request.path)

        self.middleware.fetch_signing_cert()

        self.assertEqual('/newadmin/v2.0/certificates/signing',
                         httpretty.httpretty.last_request.path)

    def test_without_prefix(self):
        self.conf['auth_admin_prefix'] = ''

        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/certificates/ca" % BASE_HOST,
                               body='FAKECA')
        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/certificates/signing" % BASE_HOST,
                               body='FAKECERT')

        self.set_middleware(conf=self.conf)

        self.middleware.fetch_ca_cert()

        self.assertEqual('/v2.0/certificates/ca',
                         httpretty.httpretty.last_request.path)

        self.middleware.fetch_signing_cert()

        self.assertEqual('/v2.0/certificates/signing',
                         httpretty.httpretty.last_request.path)


def network_error_response(method, uri, headers):
    raise auth_token.NetworkError("Network connection error.")


class v2AuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                CommonAuthTokenMiddlewareTest):
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

    def setUp(self):
        super(v2AuthTokenMiddlewareTest, self).setUp()

        self.token_dict = {
            'uuid_token_default': client_fixtures.UUID_TOKEN_DEFAULT,
            'uuid_token_unscoped': client_fixtures.UUID_TOKEN_UNSCOPED,
            'signed_token_scoped': client_fixtures.SIGNED_TOKEN_SCOPED,
            'signed_token_scoped_expired':
            client_fixtures.SIGNED_TOKEN_SCOPED_EXPIRED,
            'revoked_token': client_fixtures.REVOKED_TOKEN,
            'revoked_token_hash': client_fixtures.REVOKED_TOKEN_HASH
        }

        httpretty.httpretty.reset()
        httpretty.enable()

        httpretty.register_uri(httpretty.GET,
                               "%s/" % BASE_URI,
                               body=VERSION_LIST_v2,
                               status=300)

        httpretty.register_uri(httpretty.POST,
                               "%s/v2.0/tokens" % BASE_URI,
                               body=FAKE_ADMIN_TOKEN)

        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/tokens/revoked" % BASE_URI,
                               body=client_fixtures.SIGNED_REVOCATION_LIST,
                               status=200)

        for token in (client_fixtures.UUID_TOKEN_DEFAULT,
                      client_fixtures.UUID_TOKEN_UNSCOPED,
                      client_fixtures.UUID_TOKEN_NO_SERVICE_CATALOG):
            httpretty.register_uri(httpretty.GET,
                                   "%s/v2.0/tokens/%s" % (BASE_URI, token),
                                   body=
                                   client_fixtures.JSON_TOKEN_RESPONSES[token])

        httpretty.register_uri(httpretty.GET,
                               '%s/v2.0/tokens/%s' % (BASE_URI, ERROR_TOKEN),
                               body=network_error_response)

        self.set_middleware()

    def tearDown(self):
        httpretty.disable()
        super(v2AuthTokenMiddlewareTest, self).tearDown()

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

    def assert_valid_last_url(self, token_id):
        self.assertLastPath("/testadmin/v2.0/tokens/%s" % token_id)

    def test_default_tenant_uuid_token(self):
        self.assert_unscoped_default_tenant_auto_scopes(
            client_fixtures.UUID_TOKEN_DEFAULT)

    def test_default_tenant_signed_token(self):
        self.assert_unscoped_default_tenant_auto_scopes(
            client_fixtures.SIGNED_TOKEN_SCOPED)

    def assert_unscoped_token_receives_401(self, token):
        """Unscoped requests with no default tenant ID should be rejected."""
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = token
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 401)
        self.assertEqual(self.response_headers['WWW-Authenticate'],
                         "Keystone uri='https://keystone.example.com:1234'")

    def test_unscoped_uuid_token_receives_401(self):
        self.assert_unscoped_token_receives_401(
            client_fixtures.UUID_TOKEN_UNSCOPED)

    def test_unscoped_pki_token_receives_401(self):
        self.assert_unscoped_token_receives_401(
            client_fixtures.SIGNED_TOKEN_UNSCOPED)

    def test_request_prevent_service_catalog_injection(self):
        req = webob.Request.blank('/')
        req.headers['X-Service-Catalog'] = '[]'
        req.headers['X-Auth-Token'] = \
            client_fixtures.UUID_TOKEN_NO_SERVICE_CATALOG
        body = self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertFalse(req.headers.get('X-Service-Catalog'))
        self.assertEqual(body, ['SUCCESS'])


class CrossVersionAuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest):

    @httpretty.activate
    def test_valid_uuid_request_forced_to_2_0(self):
        """Test forcing auth_token to use lower api version.

        By installing the v3 http hander, auth_token will be get
        a version list that looks like a v3 server - from which it
        would normally chose v3.0 as the auth version.  However, here
        we specify v2.0 in the configuration - which should force
        auth_token to use that version instead.

        """
        conf = {
            'signing_dir': client_fixtures.CERTDIR,
            'auth_version': 'v2.0'
        }

        httpretty.register_uri(httpretty.GET,
                               "%s/" % BASE_URI,
                               body=VERSION_LIST_v3,
                               status=300)

        httpretty.register_uri(httpretty.POST,
                               "%s/v2.0/tokens" % BASE_URI,
                               body=FAKE_ADMIN_TOKEN)

        token = client_fixtures.UUID_TOKEN_DEFAULT
        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/tokens/%s" % (BASE_URI, token),
                               body=
                               client_fixtures.JSON_TOKEN_RESPONSES[token])

        self.set_middleware(conf=conf)

        # This tests will only work is auth_token has chosen to use the
        # lower, v2, api version
        req = webob.Request.blank('/')
        req.headers['X-Auth-Token'] = client_fixtures.UUID_TOKEN_DEFAULT
        self.middleware(req.environ, self.start_fake_response)
        self.assertEqual(self.response_status, 200)
        self.assertEqual("/testadmin/v2.0/tokens/%s" %
                         client_fixtures.UUID_TOKEN_DEFAULT,
                         httpretty.httpretty.last_request.path)


class v3AuthTokenMiddlewareTest(BaseAuthTokenMiddlewareTest,
                                CommonAuthTokenMiddlewareTest):
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
        super(v3AuthTokenMiddlewareTest, self).setUp(
            auth_version='v3.0',
            fake_app=v3FakeApp)

        self.token_dict = {
            'uuid_token_default': client_fixtures.v3_UUID_TOKEN_DEFAULT,
            'uuid_token_unscoped': client_fixtures.v3_UUID_TOKEN_UNSCOPED,
            'signed_token_scoped': client_fixtures.SIGNED_v3_TOKEN_SCOPED,
            'signed_token_scoped_expired':
            client_fixtures.SIGNED_TOKEN_SCOPED_EXPIRED,
            'revoked_token': client_fixtures.REVOKED_v3_TOKEN,
            'revoked_token_hash': client_fixtures.REVOKED_v3_TOKEN_HASH
        }

        httpretty.httpretty.reset()
        httpretty.enable()

        httpretty.register_uri(httpretty.GET,
                               "%s" % BASE_URI,
                               body=VERSION_LIST_v3,
                               status=300)

        # TODO(jamielennox): auth_token middleware uses a v2 admin token
        # regardless of the auth_version that is set.
        httpretty.register_uri(httpretty.POST,
                               "%s/v2.0/tokens" % BASE_URI,
                               body=FAKE_ADMIN_TOKEN)

        # TODO(jamielennox): there is no v3 revocation url yet, it uses v2
        httpretty.register_uri(httpretty.GET,
                               "%s/v2.0/tokens/revoked" % BASE_URI,
                               body=client_fixtures.SIGNED_REVOCATION_LIST,
                               status=200)

        httpretty.register_uri(httpretty.GET,
                               "%s/v3/auth/tokens" % BASE_URI,
                               body=self.token_response)

        self.set_middleware()

    def tearDown(self):
        httpretty.disable()
        super(v3AuthTokenMiddlewareTest, self).tearDown()

    def token_response(self, request, uri, headers):
        auth_id = request.headers.get('X-Auth-Token')
        token_id = request.headers.get('X-Subject-Token')
        self.assertEqual(auth_id, FAKE_ADMIN_TOKEN_ID)
        headers.pop('status')

        status = 200
        response = ""

        if token_id == ERROR_TOKEN:
            raise auth_token.NetworkError("Network connection error.")

        try:
            response = client_fixtures.JSON_TOKEN_RESPONSES[token_id]
        except KeyError:
            status = 404

        return status, headers, response

    def assert_valid_last_url(self, token_id):
        self.assertLastPath('/testadmin/v3/auth/tokens')

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
        self.assert_valid_request_200(client_fixtures.v3_UUID_TOKEN_UNSCOPED,
                                      with_catalog=False)
        self.assertLastPath('/testadmin/v3/auth/tokens')

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
        self.assert_valid_request_200(
            client_fixtures.v3_UUID_TOKEN_DOMAIN_SCOPED)
        self.assertLastPath('/testadmin/v3/auth/tokens')


class TokenEncodingTest(testtools.TestCase):
    def test_unquoted_token(self):
        self.assertEqual('foo%20bar', auth_token.safe_quote('foo bar'))

    def test_quoted_token(self):
        self.assertEqual('foo%20bar', auth_token.safe_quote('foo%20bar'))
