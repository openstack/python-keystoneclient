# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import os

import fixtures
import six
import testresources

from keystoneclient.common import cms
from keystoneclient.openstack.common import jsonutils
from keystoneclient.openstack.common import timeutils
from keystoneclient import utils


TESTDIR = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = os.path.normpath(os.path.join(TESTDIR, '..', '..'))
CERTDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'certs')
CMSDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'cms')
KEYDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'private')


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

        with open(os.path.join(CMSDIR, 'auth_token_scoped.pem')) as f:
            self.SIGNED_TOKEN_SCOPED = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_unscoped.pem')) as f:
            self.SIGNED_TOKEN_UNSCOPED = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_scoped.pem')) as f:
            self.SIGNED_v3_TOKEN_SCOPED = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_revoked.pem')) as f:
            self.REVOKED_TOKEN = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_scoped_expired.pem')) as f:
            self.SIGNED_TOKEN_SCOPED_EXPIRED = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_revoked.pem')) as f:
            self.REVOKED_v3_TOKEN = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'revocation_list.json')) as f:
            self.REVOCATION_LIST = jsonutils.loads(f.read())
        with open(os.path.join(CMSDIR, 'revocation_list.pem')) as f:
            self.SIGNED_REVOCATION_LIST = jsonutils.dumps({'signed': f.read()})

        self.SIGNING_CERT_FILE = os.path.join(CERTDIR, 'signing_cert.pem')
        with open(self.SIGNING_CERT_FILE) as f:
            self.SIGNING_CERT = f.read()

        self.SIGNING_KEY_FILE = os.path.join(KEYDIR, 'signing_key.pem')
        with open(self.SIGNING_KEY_FILE) as f:
            self.SIGNING_KEY = f.read()

        self.SIGNING_CA_FILE = os.path.join(CERTDIR, 'cacert.pem')
        with open(self.SIGNING_CA_FILE) as f:
            self.SIGNING_CA = f.read()

        self.UUID_TOKEN_DEFAULT = "ec6c0710ec2f471498484c1b53ab4f9d"
        self.UUID_TOKEN_NO_SERVICE_CATALOG = '8286720fbe4941e69fa8241723bb02df'
        self.UUID_TOKEN_UNSCOPED = '731f903721c14827be7b2dc912af7776'
        self.VALID_DIABLO_TOKEN = 'b0cf19b55dbb4f20a6ee18e6c6cf1726'
        self.v3_UUID_TOKEN_DEFAULT = '5603457654b346fdbb93437bfe76f2f1'
        self.v3_UUID_TOKEN_UNSCOPED = 'd34835fdaec447e695a0a024d84f8d79'
        self.v3_UUID_TOKEN_DOMAIN_SCOPED = 'e8a7b63aaa4449f38f0c5c05c3581792'

        self.REVOKED_TOKEN_HASH = utils.hash_signed_token(self.REVOKED_TOKEN)
        self.REVOKED_TOKEN_LIST = (
            {'revoked': [{'id': self.REVOKED_TOKEN_HASH,
                          'expires': timeutils.utcnow()}]})
        self.REVOKED_TOKEN_LIST_JSON = jsonutils.dumps(self.REVOKED_TOKEN_LIST)

        self.REVOKED_v3_TOKEN_HASH = utils.hash_signed_token(
            self.REVOKED_v3_TOKEN)
        self.REVOKED_v3_TOKEN_LIST = (
            {'revoked': [{'id': self.REVOKED_v3_TOKEN_HASH,
                          'expires': timeutils.utcnow()}]})
        self.REVOKED_v3_TOKEN_LIST_JSON = jsonutils.dumps(
            self.REVOKED_v3_TOKEN_LIST)

        self.SIGNED_TOKEN_SCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_SCOPED)
        self.SIGNED_TOKEN_UNSCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_UNSCOPED)
        self.SIGNED_v3_TOKEN_SCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_v3_TOKEN_SCOPED)

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

        # JSON responses keyed by token ID
        self.TOKEN_RESPONSES = {
            self.UUID_TOKEN_DEFAULT: {
                'access': {
                    'token': {
                        'id': self.UUID_TOKEN_DEFAULT,
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
            self.VALID_DIABLO_TOKEN: {
                'access': {
                    'token': {
                        'id': self.VALID_DIABLO_TOKEN,
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
            self.UUID_TOKEN_UNSCOPED: {
                'access': {
                    'token': {
                        'id': self.UUID_TOKEN_UNSCOPED,
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
            self.UUID_TOKEN_NO_SERVICE_CATALOG: {
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
            self.v3_UUID_TOKEN_DEFAULT: {
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
            self.v3_UUID_TOKEN_UNSCOPED: {
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
            self.v3_UUID_TOKEN_DOMAIN_SCOPED: {
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
            },
            self.SIGNED_TOKEN_SCOPED_KEY: {
                'access': {
                    'token': {
                        'id': self.SIGNED_TOKEN_SCOPED_KEY,
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
            },
        }

        self.JSON_TOKEN_RESPONSES = dict([(k, jsonutils.dumps(v)) for k, v in
                                          six.iteritems(self.TOKEN_RESPONSES)])


EXAMPLES_RESOURCE = testresources.FixtureResource(Examples())
