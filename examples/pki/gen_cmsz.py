#!/usr/bin/python

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

import json
import os

from keystoneclient.common import cms
from keystoneclient import utils

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


def make_filename(*args):
    return os.path.join(CURRENT_DIR, *args)


def generate_revocation_list():
    REVOKED_TOKENS = ['auth_token_revoked', 'auth_v3_token_revoked']
    revoked_list = []
    for token in REVOKED_TOKENS:
        with open(make_filename('cms', '%s.pkiz' % name), 'r') as f:
            token_data = f.read()
            id = utils.hash_signed_token(token_data.encode('utf-8'))
            revoked_list.append({
                'id': id,
                "expires": "2112-08-14T17:58:48Z"
            })
        with open(make_filename('cms', '%s.pem' % name), 'r') as f:
            pem_data = f.read()
            token_data = cms.cms_to_token(pem_data).encode('utf-8')
            id = utils.hash_signed_token(token_data)
            revoked_list.append({
                'id': id,
                "expires": "2112-08-14T17:58:48Z"
            })
    revoked_json = json.dumps({"revoked": revoked_list})
    with open(make_filename('cms', 'revocation_list.json'), 'w') as f:
        f.write(revoked_json)
    encoded = cms.pkiz_sign(revoked_json,
                            SIGNING_CERT_FILE_NAME,
                            SIGNING_KEY_FILE_NAME)
    with open(make_filename('cms', 'revocation_list.pkiz'), 'w') as f:
        f.write(encoded)

    encoded = cms.cms_sign_data(revoked_json,
                                SIGNING_CERT_FILE_NAME,
                                SIGNING_KEY_FILE_NAME)
    with open(make_filename('cms', 'revocation_list.pem'), 'w') as f:
        f.write(encoded)


CA_CERT_FILE_NAME = make_filename('certs', 'cacert.pem')
SIGNING_CERT_FILE_NAME = make_filename('certs', 'signing_cert.pem')
SIGNING_KEY_FILE_NAME = make_filename('private', 'signing_key.pem')
EXAMPLE_TOKENS = ['auth_token_revoked',
                  'auth_token_unscoped',
                  'auth_token_scoped',
                  'auth_token_scoped_expired',
                  'auth_v3_token_scoped',
                  'auth_v3_token_revoked']


# Helper script to generate the sample data for testing
# the signed tokens using the existing JSON data for the
# MII-prefixed tokens.  Uses the keys and certificates
# generated in gen_pki.sh.
def generate_der_form(name):
    derfile = make_filename('cms', '%s.der' % name)
    with open(derfile, 'w') as f:
        derform = cms.cms_sign_data(text,
                                    SIGNING_CERT_FILE_NAME,
                                    SIGNING_KEY_FILE_NAME, cms.PKIZ_CMS_FORM)
        f.write(derform)

for name in EXAMPLE_TOKENS:
    json_file = make_filename('cms', name + '.json')
    pkiz_file = make_filename('cms', name + '.pkiz')
    with open(json_file, 'r') as f:
        string_data = f.read()

    # validate the JSON
    try:
        token_data = json.loads(string_data)
    except ValueError as v:
        raise SystemExit('%s while processing token data from %s: %s' %
                         (v, json_file, string_data))

    text = json.dumps(token_data).encode('utf-8')

    # Uncomment to record the token uncompressed,
    # useful for debugging
    # generate_der_form(name)

    encoded = cms.pkiz_sign(text,
                            SIGNING_CERT_FILE_NAME,
                            SIGNING_KEY_FILE_NAME)

    # verify before writing
    cms.pkiz_verify(encoded,
                    SIGNING_CERT_FILE_NAME,
                    CA_CERT_FILE_NAME)

    with open(pkiz_file, 'w') as f:
        f.write(encoded)

    generate_revocation_list()
