# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack LLC
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

import six

from keystoneclient.common import cms
from keystoneclient.openstack.common import jsonutils
from keystoneclient.openstack.common import timeutils
from keystoneclient import utils


CLIENTDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
ROOTDIR = os.path.dirname(CLIENTDIR)
CERTDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'certs')
CMSDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'cms')


# @TODO(mordred) This should become a testresources resource attached to the
#                class
# The data for these tests are signed using openssl and are stored in files
# in the signing subdirectory.  In order to keep the values consistent between
# the tests and the signed documents, we read them in for use in the tests.
with open(os.path.join(CMSDIR, 'auth_token_scoped.pem')) as f:
    SIGNED_TOKEN_SCOPED = cms.cms_to_token(f.read())
with open(os.path.join(CMSDIR, 'auth_token_unscoped.pem')) as f:
    SIGNED_TOKEN_UNSCOPED = cms.cms_to_token(f.read())
with open(os.path.join(CMSDIR, 'auth_v3_token_scoped.pem')) as f:
    SIGNED_v3_TOKEN_SCOPED = cms.cms_to_token(f.read())
with open(os.path.join(CMSDIR, 'auth_token_revoked.pem')) as f:
    REVOKED_TOKEN = cms.cms_to_token(f.read())
with open(os.path.join(CMSDIR, 'auth_token_scoped_expired.pem')) as f:
    SIGNED_TOKEN_SCOPED_EXPIRED = cms.cms_to_token(f.read())
with open(os.path.join(CMSDIR, 'auth_v3_token_revoked.pem')) as f:
    REVOKED_v3_TOKEN = cms.cms_to_token(f.read())
with open(os.path.join(CMSDIR, 'revocation_list.json')) as f:
    REVOCATION_LIST = jsonutils.loads(f.read())
with open(os.path.join(CMSDIR, 'revocation_list.pem')) as f:
    SIGNED_REVOCATION_LIST = jsonutils.dumps({'signed': f.read()})
with open(os.path.join(CERTDIR, 'signing_cert.pem')) as f:
    SIGNING_CERT = f.read()
with open(os.path.join(CERTDIR, 'cacert.pem')) as f:
    SIGNING_CA = f.read()

UUID_TOKEN_DEFAULT = "ec6c0710ec2f471498484c1b53ab4f9d"
UUID_TOKEN_NO_SERVICE_CATALOG = '8286720fbe4941e69fa8241723bb02df'
UUID_TOKEN_UNSCOPED = '731f903721c14827be7b2dc912af7776'
VALID_DIABLO_TOKEN = 'b0cf19b55dbb4f20a6ee18e6c6cf1726'
v3_UUID_TOKEN_DEFAULT = '5603457654b346fdbb93437bfe76f2f1'
v3_UUID_TOKEN_UNSCOPED = 'd34835fdaec447e695a0a024d84f8d79'
v3_UUID_TOKEN_DOMAIN_SCOPED = 'e8a7b63aaa4449f38f0c5c05c3581792'

REVOKED_TOKEN_HASH = utils.hash_signed_token(REVOKED_TOKEN)
REVOKED_TOKEN_LIST = {'revoked': [{'id': REVOKED_TOKEN_HASH,
                                   'expires': timeutils.utcnow()}]}
REVOKED_TOKEN_LIST_JSON = jsonutils.dumps(REVOKED_TOKEN_LIST)

REVOKED_v3_TOKEN_HASH = utils.hash_signed_token(REVOKED_v3_TOKEN)
REVOKED_v3_TOKEN_LIST = {'revoked': [{'id': REVOKED_v3_TOKEN_HASH,
                                      'expires': timeutils.utcnow()}]}
REVOKED_v3_TOKEN_LIST_JSON = jsonutils.dumps(REVOKED_v3_TOKEN_LIST)

SIGNED_TOKEN_SCOPED_KEY = cms.cms_hash_token(SIGNED_TOKEN_SCOPED)
SIGNED_TOKEN_UNSCOPED_KEY = cms.cms_hash_token(SIGNED_TOKEN_UNSCOPED)
SIGNED_v3_TOKEN_SCOPED_KEY = cms.cms_hash_token(SIGNED_v3_TOKEN_SCOPED)

INVALID_SIGNED_TOKEN = \
    "MIIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" \
    "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB" \
    "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC" \
    "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD" \
    "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE" \
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF" \
    "0000000000000000000000000000000000000000000000000000000000000000" \
    "1111111111111111111111111111111111111111111111111111111111111111" \
    "2222222222222222222222222222222222222222222222222222222222222222" \
    "3333333333333333333333333333333333333333333333333333333333333333" \
    "4444444444444444444444444444444444444444444444444444444444444444" \
    "5555555555555555555555555555555555555555555555555555555555555555" \
    "6666666666666666666666666666666666666666666666666666666666666666" \
    "7777777777777777777777777777777777777777777777777777777777777777" \
    "8888888888888888888888888888888888888888888888888888888888888888" \
    "9999999999999999999999999999999999999999999999999999999999999999" \
    "0000000000000000000000000000000000000000000000000000000000000000" \


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
    },
    SIGNED_TOKEN_SCOPED_KEY: {
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
    },
    SIGNED_TOKEN_UNSCOPED_KEY: {
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
    },
    SIGNED_v3_TOKEN_SCOPED_KEY: {
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


JSON_TOKEN_RESPONSES = dict([(k, jsonutils.dumps(v)) for k, v in
                             six.iteritems(TOKEN_RESPONSES)])
