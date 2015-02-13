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

from tempest_lib.cli import base


class TestCase(base.ClientTestBase):

    def _get_clients(self):
        path = os.path.join(os.path.abspath('.'), '.tox/functional/bin')
        cli_dir = os.environ.get('OS_KEYSTONECLIENT_EXEC_DIR', path)

        return base.CLIClient(
            username=os.environ.get('OS_USERNAME'),
            password=os.environ.get('OS_PASSWORD'),
            tenant_name=os.environ.get('OS_TENANT_NAME'),
            uri=os.environ.get('OS_AUTH_URL'),
            cli_dir=cli_dir)

    def keystone(self, *args, **kwargs):
        return self.clients.keystone(*args, **kwargs)
