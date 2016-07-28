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

import uuid

from keystoneauth1.exceptions import http

from keystoneclient.tests.functional import base
from keystoneclient.tests.functional.v3 import client_fixtures as fixtures


class CredentialsTestCase(base.V3ClientTestCase):

    def check_credential(self, credential, credential_ref=None):
        self.assertIsNotNone(credential.id)
        self.assertIn('self', credential.links)
        self.assertIn('/credentials/' + credential.id,
                      credential.links['self'])

        if credential_ref:
            self.assertEqual(credential_ref['user'], credential.user_id)
            self.assertEqual(credential_ref['type'], credential.type)
            self.assertEqual(credential_ref['blob'], credential.blob)

            # There is no guarantee below attributes are present in credential
            if credential_ref['type'] == 'ec2' or hasattr(credential_ref,
                                                          'project'):
                self.assertEqual(credential_ref['project'],
                                 credential.project_id)

        else:
            # Only check remaining mandatory attributes
            self.assertIsNotNone(credential.user_id)
            self.assertIsNotNone(credential.type)
            self.assertIsNotNone(credential.blob)
            if credential.type == 'ec2':
                self.assertIsNotNone(credential.project_id)

    def test_create_credential_of_cert_type(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)

        credential_ref = {'user': user.id,
                          'type': 'cert',
                          'blob': uuid.uuid4().hex}
        credential = self.client.credentials.create(**credential_ref)

        self.addCleanup(self.client.credentials.delete, credential)
        self.check_credential(credential, credential_ref)

    def test_create_credential_of_ec2_type(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)

        # project is mandatory attribute if the credential type is ec2
        credential_ref = {'user': user.id,
                          'type': 'ec2',
                          'blob': ("{\"access\":\"" + uuid.uuid4().hex +
                                   "\",\"secret\":\"secretKey\"}")}
        self.assertRaises(http.BadRequest,
                          self.client.credentials.create,
                          **credential_ref)

        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        credential_ref = {'user': user.id,
                          'type': 'ec2',
                          'blob': ("{\"access\":\"" + uuid.uuid4().hex +
                                   "\",\"secret\":\"secretKey\"}"),
                          'project': project.id}
        credential = self.client.credentials.create(**credential_ref)

        self.addCleanup(self.client.credentials.delete, credential)
        self.check_credential(credential, credential_ref)

    def test_create_credential_of_totp_type(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)

        credential_ref = {'user': user.id,
                          'type': 'totp',
                          'blob': uuid.uuid4().hex}
        credential = self.client.credentials.create(**credential_ref)

        self.addCleanup(self.client.credentials.delete, credential)
        self.check_credential(credential, credential_ref)

    def test_get_credential(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)
        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        for credential_type in ['cert', 'ec2', 'totp']:
            credential = fixtures.Credential(self.client, user=user.id,
                                             type=credential_type,
                                             project=project.id)
            self.useFixture(credential)

            credential_ret = self.client.credentials.get(credential.id)
            self.check_credential(credential_ret, credential.ref)

    def test_list_credentials(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)

        cert_credential = fixtures.Credential(self.client, user=user.id,
                                              type='cert')
        self.useFixture(cert_credential)

        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)
        ec2_credential = fixtures.Credential(self.client, user=user.id,
                                             type='ec2', project=project.id)
        self.useFixture(ec2_credential)

        totp_credential = fixtures.Credential(self.client, user=user.id,
                                              type='totp')
        self.useFixture(totp_credential)

        credentials = self.client.credentials.list()

        # All credentials are valid
        for credential in credentials:
            self.check_credential(credential)

        self.assertIn(cert_credential.entity, credentials)
        self.assertIn(ec2_credential.entity, credentials)
        self.assertIn(totp_credential.entity, credentials)

    def test_update_credential(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)

        new_user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(new_user)
        new_project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(new_project)

        credential = fixtures.Credential(self.client, user=user.id,
                                         type='cert')
        self.useFixture(credential)

        new_type = 'ec2'
        new_blob = ("{\"access\":\"" + uuid.uuid4().hex +
                    "\",\"secret\":\"secretKey\"}")

        credential_ret = self.client.credentials.update(credential.id,
                                                        user=new_user.id,
                                                        type=new_type,
                                                        blob=new_blob,
                                                        project=new_project.id)

        credential.ref.update({'user': new_user.id, 'type': new_type,
                               'blob': new_blob, 'project': new_project.id})
        self.check_credential(credential_ret, credential.ref)

    def test_delete_credential(self):
        user = fixtures.User(self.client, self.project_domain_id)
        self.useFixture(user)
        project = fixtures.Project(self.client, self.project_domain_id)
        self.useFixture(project)

        for credential_type in ['cert', 'ec2', 'totp']:

            if credential_type == 'ec2':
                blob_value = ("{\"access\":\"" + uuid.uuid4().hex +
                              "\",\"secret\":\"secretKey\"}")
            else:
                blob_value = uuid.uuid4().hex

            credential = self.client.credentials.create(user=user.id,
                                                        type=credential_type,
                                                        blob=blob_value,
                                                        project=project.id)
            self.client.credentials.delete(credential.id)
            self.assertRaises(http.NotFound,
                              self.client.credentials.get,
                              credential.id)
