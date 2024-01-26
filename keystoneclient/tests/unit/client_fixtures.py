# Copyright 2013 OpenStack Foundation
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

import contextlib
import os
import uuid
import warnings

import fixtures
from keystoneauth1 import fixture
from keystoneauth1 import identity as ksa_identity
from keystoneauth1 import session as ksa_session
from oslo_serialization import jsonutils
from oslo_utils import timeutils
import testresources

from keystoneclient.auth import identity as ksc_identity
from keystoneclient.common import cms
from keystoneclient import session as ksc_session
from keystoneclient import utils
from keystoneclient.v2_0 import client as v2_client
from keystoneclient.v3 import client as v3_client


TEST_ROOT_URL = 'http://127.0.0.1:5000/'

TESTDIR = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = os.path.normpath(os.path.join(TESTDIR, '..', '..', '..'))
CERTDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'certs')
CMSDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'cms')
KEYDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'private')


class BaseFixture(fixtures.Fixture):

    TEST_ROOT_URL = TEST_ROOT_URL

    def __init__(self, requests, deprecations):
        super(BaseFixture, self).__init__()
        self.requests = requests
        self.deprecations = deprecations
        self.user_id = uuid.uuid4().hex
        self.client = self.new_client()


class BaseV2(BaseFixture):

    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v2.0')


class OriginalV2(BaseV2):

    def new_client(self):
        # Creating a Client not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            return v2_client.Client(username=uuid.uuid4().hex,
                                    user_id=self.user_id,
                                    token=uuid.uuid4().hex,
                                    tenant_name=uuid.uuid4().hex,
                                    auth_url=self.TEST_URL,
                                    endpoint=self.TEST_URL)


class KscSessionV2(BaseV2):

    def new_client(self):
        t = fixture.V2Token(user_id=self.user_id)
        t.set_scope()

        s = t.add_service('identity')
        s.add_endpoint(self.TEST_URL)

        d = fixture.V2Discovery(self.TEST_URL)

        self.requests.register_uri('POST', self.TEST_URL + '/tokens', json=t)

        # NOTE(jamielennox): Because of the versioned URL hack here even though
        # the V2 URL will be in the service catalog it will be the root URL
        # that will be queried for discovery.
        self.requests.register_uri('GET', self.TEST_ROOT_URL,
                                   json={'version': d})

        with self.deprecations.expect_deprecations_here():
            a = ksc_identity.V2Password(username=uuid.uuid4().hex,
                                        password=uuid.uuid4().hex,
                                        auth_url=self.TEST_URL)

            s = ksc_session.Session(auth=a)

        return v2_client.Client(session=s)


class KsaSessionV2(BaseV2):

    def new_client(self):
        t = fixture.V2Token(user_id=self.user_id)
        t.set_scope()

        s = t.add_service('identity')
        s.add_endpoint(self.TEST_URL)

        d = fixture.V2Discovery(self.TEST_URL)

        self.requests.register_uri('POST', self.TEST_URL + '/tokens', json=t)

        # NOTE(jamielennox): Because of the versioned URL hack here even though
        # the V2 URL will be in the service catalog it will be the root URL
        # that will be queried for discovery.
        self.requests.register_uri('GET', self.TEST_ROOT_URL,
                                   json={'version': d})

        a = ksa_identity.V2Password(username=uuid.uuid4().hex,
                                    password=uuid.uuid4().hex,
                                    auth_url=self.TEST_URL)
        s = ksa_session.Session(auth=a)
        return v2_client.Client(session=s)


class BaseV3(BaseFixture):

    TEST_URL = '%s%s' % (TEST_ROOT_URL, 'v3')


class OriginalV3(BaseV3):

    def new_client(self):
        # Creating a Client not using session is deprecated.
        with self.deprecations.expect_deprecations_here():
            return v3_client.Client(username=uuid.uuid4().hex,
                                    user_id=self.user_id,
                                    token=uuid.uuid4().hex,
                                    tenant_name=uuid.uuid4().hex,
                                    auth_url=self.TEST_URL,
                                    endpoint=self.TEST_URL)


class KscSessionV3(BaseV3):

    def new_client(self):
        t = fixture.V3Token(user_id=self.user_id)
        t.set_project_scope()

        s = t.add_service('identity')
        s.add_standard_endpoints(public=self.TEST_URL,
                                 admin=self.TEST_URL)

        d = fixture.V3Discovery(self.TEST_URL)

        headers = {'X-Subject-Token': uuid.uuid4().hex}
        self.requests.register_uri('POST',
                                   self.TEST_URL + '/auth/tokens',
                                   headers=headers,
                                   json=t)
        self.requests.register_uri('GET', self.TEST_URL, json={'version': d})

        with self.deprecations.expect_deprecations_here():
            a = ksc_identity.V3Password(username=uuid.uuid4().hex,
                                        password=uuid.uuid4().hex,
                                        user_domain_id=uuid.uuid4().hex,
                                        auth_url=self.TEST_URL)

            s = ksc_session.Session(auth=a)

        return v3_client.Client(session=s)


class KsaSessionV3(BaseV3):

    def new_client(self):
        t = fixture.V3Token(user_id=self.user_id)
        t.set_project_scope()

        s = t.add_service('identity')
        s.add_standard_endpoints(public=self.TEST_URL,
                                 admin=self.TEST_URL)

        d = fixture.V3Discovery(self.TEST_URL)

        headers = {'X-Subject-Token': uuid.uuid4().hex}
        self.requests.register_uri('POST',
                                   self.TEST_URL + '/auth/tokens',
                                   headers=headers,
                                   json=t)
        self.requests.register_uri('GET', self.TEST_URL, json={'version': d})

        a = ksa_identity.V3Password(username=uuid.uuid4().hex,
                                    password=uuid.uuid4().hex,
                                    user_domain_id=uuid.uuid4().hex,
                                    auth_url=self.TEST_URL)
        s = ksa_session.Session(auth=a)
        return v3_client.Client(session=s)


def _hash_signed_token_safe(signed_text, **kwargs):
    if isinstance(signed_text, str):
        signed_text = signed_text.encode('utf-8')
    return utils.hash_signed_token(signed_text, **kwargs)


class Examples(fixtures.Fixture):
    """Example tokens and certs loaded from the examples directory.

    To use this class correctly, the module needs to override the test suite
    class to use testresources.OptimisingTestSuite (otherwise the files will
    be read on every test). This is done by defining a load_tests function
    in the module, like this:

    def load_tests(loader, tests, pattern):
        return testresources.OptimisingTestSuite(tests)

    (see http://docs.python.org/2/library/unittest.html#load-tests-protocol )

    """

    def setUp(self):
        super(Examples, self).setUp()

        # The data for several tests are signed using openssl and are stored in
        # files in the signing subdirectory.  In order to keep the values
        # consistent between the tests and the signed documents, we read them
        # in for use in the tests.
        with open(os.path.join(CMSDIR, 'auth_token_scoped.json')) as f:
            self.TOKEN_SCOPED_DATA = cms.cms_to_token(f.read())

        with open(os.path.join(CMSDIR, 'auth_token_scoped.pem')) as f:
            self.SIGNED_TOKEN_SCOPED = cms.cms_to_token(f.read())
        self.SIGNED_TOKEN_SCOPED_HASH = _hash_signed_token_safe(
            self.SIGNED_TOKEN_SCOPED)
        self.SIGNED_TOKEN_SCOPED_HASH_SHA256 = _hash_signed_token_safe(
            self.SIGNED_TOKEN_SCOPED, mode='sha256')
        with open(os.path.join(CMSDIR, 'auth_token_unscoped.pem')) as f:
            self.SIGNED_TOKEN_UNSCOPED = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_scoped.pem')) as f:
            self.SIGNED_v3_TOKEN_SCOPED = cms.cms_to_token(f.read())
        self.SIGNED_v3_TOKEN_SCOPED_HASH = _hash_signed_token_safe(
            self.SIGNED_v3_TOKEN_SCOPED)
        self.SIGNED_v3_TOKEN_SCOPED_HASH_SHA256 = _hash_signed_token_safe(
            self.SIGNED_v3_TOKEN_SCOPED, mode='sha256')
        with open(os.path.join(CMSDIR, 'auth_token_revoked.pem')) as f:
            self.REVOKED_TOKEN = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_scoped_expired.pem')) as f:
            self.SIGNED_TOKEN_SCOPED_EXPIRED = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_revoked.pem')) as f:
            self.REVOKED_v3_TOKEN = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_scoped.pkiz')) as f:
            self.SIGNED_TOKEN_SCOPED_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_unscoped.pkiz')) as f:
            self.SIGNED_TOKEN_UNSCOPED_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_scoped.pkiz')) as f:
            self.SIGNED_v3_TOKEN_SCOPED_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_revoked.pkiz')) as f:
            self.REVOKED_TOKEN_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR,
                               'auth_token_scoped_expired.pkiz')) as f:
            self.SIGNED_TOKEN_SCOPED_EXPIRED_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_revoked.pkiz')) as f:
            self.REVOKED_v3_TOKEN_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'revocation_list.json')) as f:
            self.REVOCATION_LIST = jsonutils.loads(f.read())
        with open(os.path.join(CMSDIR, 'revocation_list.pem')) as f:
            self.SIGNED_REVOCATION_LIST = jsonutils.dumps({'signed': f.read()})

        self.SIGNING_CERT_FILE = os.path.join(CERTDIR, 'signing_cert.pem')
        with open(self.SIGNING_CERT_FILE) as f:
            self.SIGNING_CERT = f.read()

        self.KERBEROS_BIND = 'USER@REALM'

        self.SIGNING_KEY_FILE = os.path.join(KEYDIR, 'signing_key.pem')
        with open(self.SIGNING_KEY_FILE) as f:
            self.SIGNING_KEY = f.read()

        self.SIGNING_CA_FILE = os.path.join(CERTDIR, 'cacert.pem')
        with open(self.SIGNING_CA_FILE) as f:
            self.SIGNING_CA = f.read()

        self.UUID_TOKEN_DEFAULT = "ec6c0710ec2f471498484c1b53ab4f9d"
        self.UUID_TOKEN_NO_SERVICE_CATALOG = '8286720fbe4941e69fa8241723bb02df'
        self.UUID_TOKEN_UNSCOPED = '731f903721c14827be7b2dc912af7776'
        self.UUID_TOKEN_BIND = '3fc54048ad64405c98225ce0897af7c5'
        self.UUID_TOKEN_UNKNOWN_BIND = '8885fdf4d42e4fb9879e6379fa1eaf48'
        self.VALID_DIABLO_TOKEN = 'b0cf19b55dbb4f20a6ee18e6c6cf1726'
        self.v3_UUID_TOKEN_DEFAULT = '5603457654b346fdbb93437bfe76f2f1'
        self.v3_UUID_TOKEN_UNSCOPED = 'd34835fdaec447e695a0a024d84f8d79'
        self.v3_UUID_TOKEN_DOMAIN_SCOPED = 'e8a7b63aaa4449f38f0c5c05c3581792'
        self.v3_UUID_TOKEN_BIND = '2f61f73e1c854cbb9534c487f9bd63c2'
        self.v3_UUID_TOKEN_UNKNOWN_BIND = '7ed9781b62cd4880b8d8c6788ab1d1e2'

        revoked_token = self.REVOKED_TOKEN
        if isinstance(revoked_token, str):
            revoked_token = revoked_token.encode('utf-8')
        self.REVOKED_TOKEN_HASH = utils.hash_signed_token(revoked_token)
        self.REVOKED_TOKEN_HASH_SHA256 = utils.hash_signed_token(revoked_token,
                                                                 mode='sha256')
        self.REVOKED_TOKEN_LIST = (
            {'revoked': [{'id': self.REVOKED_TOKEN_HASH,
                          'expires': timeutils.utcnow()}]})
        self.REVOKED_TOKEN_LIST_JSON = jsonutils.dumps(self.REVOKED_TOKEN_LIST)

        revoked_v3_token = self.REVOKED_v3_TOKEN
        if isinstance(revoked_v3_token, str):
            revoked_v3_token = revoked_v3_token.encode('utf-8')
        self.REVOKED_v3_TOKEN_HASH = utils.hash_signed_token(revoked_v3_token)
        hash = utils.hash_signed_token(revoked_v3_token, mode='sha256')
        self.REVOKED_v3_TOKEN_HASH_SHA256 = hash
        self.REVOKED_v3_TOKEN_LIST = (
            {'revoked': [{'id': self.REVOKED_v3_TOKEN_HASH,
                          'expires': timeutils.utcnow()}]})
        self.REVOKED_v3_TOKEN_LIST_JSON = jsonutils.dumps(
            self.REVOKED_v3_TOKEN_LIST)

        revoked_token_pkiz = self.REVOKED_TOKEN_PKIZ
        if isinstance(revoked_token_pkiz, str):
            revoked_token_pkiz = revoked_token_pkiz.encode('utf-8')
        self.REVOKED_TOKEN_PKIZ_HASH = utils.hash_signed_token(
            revoked_token_pkiz)
        revoked_v3_token_pkiz = self.REVOKED_v3_TOKEN_PKIZ
        if isinstance(revoked_v3_token_pkiz, str):
            revoked_v3_token_pkiz = revoked_v3_token_pkiz.encode('utf-8')
        self.REVOKED_v3_PKIZ_TOKEN_HASH = utils.hash_signed_token(
            revoked_v3_token_pkiz)

        self.REVOKED_TOKEN_PKIZ_LIST = (
            {'revoked': [{'id': self.REVOKED_TOKEN_PKIZ_HASH,
                          'expires': timeutils.utcnow()},
                         {'id': self.REVOKED_v3_PKIZ_TOKEN_HASH,
                          'expires': timeutils.utcnow()},
                         ]})
        self.REVOKED_TOKEN_PKIZ_LIST_JSON = jsonutils.dumps(
            self.REVOKED_TOKEN_PKIZ_LIST)

        self.SIGNED_TOKEN_SCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_SCOPED)
        self.SIGNED_TOKEN_UNSCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_UNSCOPED)
        self.SIGNED_v3_TOKEN_SCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_v3_TOKEN_SCOPED)

        self.SIGNED_TOKEN_SCOPED_PKIZ_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_SCOPED_PKIZ)
        self.SIGNED_TOKEN_UNSCOPED_PKIZ_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_UNSCOPED_PKIZ)
        self.SIGNED_v3_TOKEN_SCOPED_PKIZ_KEY = cms.cms_hash_token(
            self.SIGNED_v3_TOKEN_SCOPED_PKIZ)

        self.INVALID_SIGNED_TOKEN = (
            "MIIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
            "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
            "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
            "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
            "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "1111111111111111111111111111111111111111111111111111111111111111"
            "2222222222222222222222222222222222222222222222222222222222222222"
            "3333333333333333333333333333333333333333333333333333333333333333"
            "4444444444444444444444444444444444444444444444444444444444444444"
            "5555555555555555555555555555555555555555555555555555555555555555"
            "6666666666666666666666666666666666666666666666666666666666666666"
            "7777777777777777777777777777777777777777777777777777777777777777"
            "8888888888888888888888888888888888888888888888888888888888888888"
            "9999999999999999999999999999999999999999999999999999999999999999"
            "0000000000000000000000000000000000000000000000000000000000000000")

        self.INVALID_SIGNED_PKIZ_TOKEN = (
            "PKIZ_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
            "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
            "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
            "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
            "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "1111111111111111111111111111111111111111111111111111111111111111"
            "2222222222222222222222222222222222222222222222222222222222222222"
            "3333333333333333333333333333333333333333333333333333333333333333"
            "4444444444444444444444444444444444444444444444444444444444444444"
            "5555555555555555555555555555555555555555555555555555555555555555"
            "6666666666666666666666666666666666666666666666666666666666666666"
            "7777777777777777777777777777777777777777777777777777777777777777"
            "8888888888888888888888888888888888888888888888888888888888888888"
            "9999999999999999999999999999999999999999999999999999999999999999"
            "0000000000000000000000000000000000000000000000000000000000000000")

        # JSON responses keyed by token ID
        self.TOKEN_RESPONSES = {
            self.UUID_TOKEN_DEFAULT: {
                'access': {
                    'token': {
                        'id': self.UUID_TOKEN_DEFAULT,
                        'expires': '2999-01-01T00:00:10.000123Z',
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
            self.VALID_DIABLO_TOKEN: {
                'access': {
                    'token': {
                        'id': self.VALID_DIABLO_TOKEN,
                        'expires': '2999-01-01T00:00:10.000123Z',
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
            self.UUID_TOKEN_UNSCOPED: {
                'access': {
                    'token': {
                        'id': self.UUID_TOKEN_UNSCOPED,
                        'expires': '2999-01-01T00:00:10.000123Z',
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
            self.UUID_TOKEN_NO_SERVICE_CATALOG: {
                'access': {
                    'token': {
                        'id': 'valid-token',
                        'expires': '2999-01-01T00:00:10.000123Z',
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
            self.UUID_TOKEN_BIND: {
                'access': {
                    'token': {
                        'bind': {'kerberos': self.KERBEROS_BIND},
                        'id': self.UUID_TOKEN_BIND,
                        'expires': '2999-01-01T00:00:10.000123Z',
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
            self.UUID_TOKEN_UNKNOWN_BIND: {
                'access': {
                    'token': {
                        'bind': {'FOO': 'BAR'},
                        'id': self.UUID_TOKEN_UNKNOWN_BIND,
                        'expires': '2999-01-01T00:00:10.000123Z',
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
            self.v3_UUID_TOKEN_DEFAULT: {
                'token': {
                    'expires_at': '2999-01-01T00:00:10.000123Z',
                    'methods': ['password'],
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
            self.v3_UUID_TOKEN_UNSCOPED: {
                'token': {
                    'expires_at': '2999-01-01T00:00:10.000123Z',
                    'methods': ['password'],
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
            self.v3_UUID_TOKEN_DOMAIN_SCOPED: {
                'token': {
                    'expires_at': '2999-01-01T00:00:10.000123Z',
                    'methods': ['password'],
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
            },
            self.SIGNED_TOKEN_SCOPED_KEY: {
                'access': {
                    'token': {
                        'id': self.SIGNED_TOKEN_SCOPED_KEY,
                        'expires': '2999-01-01T00:00:10.000123Z',
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
            },
            self.SIGNED_TOKEN_UNSCOPED_KEY: {
                'access': {
                    'token': {
                        'id': self.SIGNED_TOKEN_UNSCOPED_KEY,
                        'expires': '2999-01-01T00:00:10.000123Z',
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
            self.SIGNED_v3_TOKEN_SCOPED_KEY: {
                'token': {
                    'expires_at': '2999-01-01T00:00:10.000123Z',
                    'methods': ['password'],
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
            },
            self.v3_UUID_TOKEN_BIND: {
                'token': {
                    'bind': {'kerberos': self.KERBEROS_BIND},
                    'methods': ['password'],
                    'expires_at': '2999-01-01T00:00:10.000123Z',
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
            self.v3_UUID_TOKEN_UNKNOWN_BIND: {
                'token': {
                    'bind': {'FOO': 'BAR'},
                    'expires_at': '2999-01-01T00:00:10.000123Z',
                    'methods': ['password'],
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
        }
        self.TOKEN_RESPONSES[self.SIGNED_TOKEN_SCOPED_PKIZ_KEY] = (
            self.TOKEN_RESPONSES[self.SIGNED_TOKEN_SCOPED_KEY])
        self.TOKEN_RESPONSES[self.SIGNED_TOKEN_UNSCOPED_PKIZ_KEY] = (
            self.TOKEN_RESPONSES[self.SIGNED_TOKEN_UNSCOPED_KEY])
        self.TOKEN_RESPONSES[self.SIGNED_v3_TOKEN_SCOPED_PKIZ_KEY] = (
            self.TOKEN_RESPONSES[self.SIGNED_v3_TOKEN_SCOPED_KEY])

        self.JSON_TOKEN_RESPONSES = dict([(k, jsonutils.dumps(v)) for k, v in
                                          self.TOKEN_RESPONSES.items()])


EXAMPLES_RESOURCE = testresources.FixtureResource(Examples())


class Deprecations(fixtures.Fixture):
    def setUp(self):
        super(Deprecations, self).setUp()

        # If keystoneclient calls any deprecated function this will raise an
        # exception.
        warnings.filterwarnings('error', category=DeprecationWarning,
                                module='^keystoneclient\\.')
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                                module='^debtcollector\\.')
        self.addCleanup(warnings.resetwarnings)

    def expect_deprecations(self):
        """Call this if the test expects to call deprecated function."""
        warnings.resetwarnings()
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                                module='^keystoneclient\\.')
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                                module='^debtcollector\\.')

    @contextlib.contextmanager
    def expect_deprecations_here(self):
        warnings.resetwarnings()
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                                module='^keystoneclient\\.')
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                                module='^debtcollector\\.')
        yield
        warnings.resetwarnings()
        warnings.filterwarnings('error', category=DeprecationWarning,
                                module='^keystoneclient\\.')
        warnings.filterwarnings('ignore', category=DeprecationWarning,
                                module='^debtcollector\\.')
