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

import testtools

from keystoneclient import client
import os_client_config


class ClientTestCase(testtools.TestCase):

    def setUp(self):
        super(ClientTestCase, self).setUp()

        self.client = self.get_client()

    def get_client(self):
        """Creates a keystoneclient instance to run functional tests

        The client is instantiated via os-client-config either based on a
        clouds.yaml config file or from the environment variables.

        First, look for a 'functional_admin' cloud, as this is a cloud that the
        user may have defined for functional testing with admin credentials. If
        that is not found, check for the 'devstack-admin' cloud. Finally, fall
        back to looking for environment variables.

        """
        IDENTITY_CLIENT = 'identity'
        OPENSTACK_CLOUDS = ('functional_admin', 'devstack-admin', 'envvars')

        for cloud in OPENSTACK_CLOUDS:
            try:
                return os_client_config.make_client(
                    IDENTITY_CLIENT, client.Client, cloud=cloud,
                    identity_api_version=self.version)
            except os_client_config.exceptions.OpenStackConfigException:
                pass

        raise Exception("Could not find any cloud definition for clouds named"
                        " functional_admin or devstack-admin. Check your"
                        " clouds.yaml file or your envvars and try again.")


class V3ClientTestCase(ClientTestCase):
    version = '3'


class V2ClientTestCase(ClientTestCase):
    version = '2.0'
