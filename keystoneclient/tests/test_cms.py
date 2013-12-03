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

import os
import subprocess

import mock

from keystoneclient.common import cms
from keystoneclient import exceptions
from keystoneclient.tests import client_fixtures
from keystoneclient.tests import utils


class CMSTest(utils.TestCase):

    """Unit tests for the keystoneclient.common.cms module."""

    def test_cms_verify(self):
        self.assertRaises(exceptions.CertificateConfigError,
                          cms.cms_verify,
                          'data',
                          'no_exist_cert_file',
                          'no_exist_ca_file')

    def test_token_to_cms_to_token(self):
        with open(os.path.join(client_fixtures.CMSDIR,
                               'auth_token_scoped.pem')) as f:
            AUTH_TOKEN_SCOPED_CMS = f.read()

        self.assertEqual(cms.token_to_cms(client_fixtures.SIGNED_TOKEN_SCOPED),
                         AUTH_TOKEN_SCOPED_CMS)

        tok = cms.cms_to_token(cms.token_to_cms(
            client_fixtures.SIGNED_TOKEN_SCOPED))
        self.assertEqual(tok, client_fixtures.SIGNED_TOKEN_SCOPED)

    def test_ans1_token(self):
        self.assertTrue(cms.is_ans1_token(client_fixtures.SIGNED_TOKEN_SCOPED))
        self.assertFalse(cms.is_ans1_token('FOOBAR'))

    def test_cms_sign_token_no_files(self):
        self.assertRaises(subprocess.CalledProcessError,
                          cms.cms_sign_token,
                          client_fixtures.SIGNED_TOKEN_SCOPED,
                          '/no/such/file', '/no/such/key')

    def test_cms_sign_token_success(self):
        self.assertTrue(
            cms.cms_sign_token(client_fixtures.SIGNED_TOKEN_SCOPED,
                               client_fixtures.SIGNING_CERT_FILE,
                               client_fixtures.SIGNING_KEY_FILE))

    def test_cms_verify_token_no_files(self):
        self.assertRaises(exceptions.CertificateConfigError,
                          cms.cms_verify,
                          client_fixtures.SIGNED_TOKEN_SCOPED,
                          '/no/such/file', '/no/such/key')

    def test_cms_verify_token_no_oserror(self):
        import errno

        def raise_OSError(*args):
            e = OSError()
            e.errno = errno.EPIPE
            raise e

        with mock.patch('subprocess.Popen.communicate', new=raise_OSError):
            try:
                cms.cms_verify("x", '/no/such/file', '/no/such/key')
            except subprocess.CalledProcessError as e:
                self.assertIn('/no/such/file', e.output)
                self.assertIn('Hit OSError ', e.output)
            else:
                self.fail('Expected subprocess.CalledProcessError')

    def test_cms_verify_token_scoped(self):
        cms_content = cms.token_to_cms(client_fixtures.SIGNED_TOKEN_SCOPED)
        self.assertTrue(cms.cms_verify(cms_content,
                                       client_fixtures.SIGNING_CERT_FILE,
                                       client_fixtures.SIGNING_CA_FILE))

    def test_cms_verify_token_scoped_expired(self):
        cms_content = cms.token_to_cms(
            client_fixtures.SIGNED_TOKEN_SCOPED_EXPIRED)
        self.assertTrue(cms.cms_verify(cms_content,
                                       client_fixtures.SIGNING_CERT_FILE,
                                       client_fixtures.SIGNING_CA_FILE))

    def test_cms_verify_token_unscoped(self):
        cms_content = cms.token_to_cms(client_fixtures.SIGNED_TOKEN_UNSCOPED)
        self.assertTrue(cms.cms_verify(cms_content,
                                       client_fixtures.SIGNING_CERT_FILE,
                                       client_fixtures.SIGNING_CA_FILE))

    def test_cms_verify_token_v3_scoped(self):
        cms_content = cms.token_to_cms(client_fixtures.SIGNED_v3_TOKEN_SCOPED)
        self.assertTrue(cms.cms_verify(cms_content,
                                       client_fixtures.SIGNING_CERT_FILE,
                                       client_fixtures.SIGNING_CA_FILE))
