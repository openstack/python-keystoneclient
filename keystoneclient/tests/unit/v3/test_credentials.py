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

import uuid

from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import credentials


class CredentialTests(utils.ClientTestCase, utils.CrudTests):
    def setUp(self):
        super(CredentialTests, self).setUp()
        self.key = 'credential'
        self.collection_key = 'credentials'
        self.model = credentials.Credential
        self.manager = self.client.credentials

    def new_ref(self, **kwargs):
        kwargs = super(CredentialTests, self).new_ref(**kwargs)
        kwargs.setdefault('blob', uuid.uuid4().hex)
        kwargs.setdefault('project_id', uuid.uuid4().hex)
        kwargs.setdefault('type', uuid.uuid4().hex)
        kwargs.setdefault('user_id', uuid.uuid4().hex)
        return kwargs
