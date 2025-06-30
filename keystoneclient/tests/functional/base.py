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

from openstack import config as occ
import openstack.exceptions
import testtools

from keystoneclient import client

IDENTITY_CLIENT = 'identity'
OPENSTACK_CLOUDS = ('functional_admin', 'devstack-admin', 'envvars')


def get_client(version):
    """Create a keystoneclient instance to run functional tests.

    The client is instantiated either based on a clouds.yaml config file or
    from the environment variables.

    First, look for a 'functional_admin' cloud, as this is a cloud that the
    user may have defined for functional testing with admin credentials. If
    that is not found, check for the 'devstack-admin' cloud. Finally, fall
    back to looking for environment variables.

    """
    for cloud in OPENSTACK_CLOUDS:
        try:
            cloud_config = occ.OpenStackConfig().get_one(
                cloud=cloud, identity_api_version=version)
            endpoint = cloud_config.get_session_endpoint(IDENTITY_CLIENT)
            return client.Client(
                version=version,
                session=cloud_config.get_session(),
                endpoint=endpoint)
        except openstack.exceptions.ConfigException:
            pass

    raise Exception("Could not find any cloud definition for clouds named"
                    " functional_admin or devstack-admin. Check your"
                    " clouds.yaml file or your envvars and try again.")


class ClientTestCase(testtools.TestCase):

    def setUp(self):
        super(ClientTestCase, self).setUp()

        if not self.auth_ref.project_scoped:
            raise Exception("Could not run functional tests, which are "
                            "run based on the scope provided for "
                            "authentication. Please provide a project "
                            "scope information.")

    @property
    def client(self):
        if not hasattr(self, '_client'):
            self._client = get_client(self.version)

        return self._client

    @property
    def auth_ref(self):
        return self.client.session.auth.get_auth_ref(self.client.session)

    @property
    def project_domain_id(self):
        return self.auth_ref.project_domain_id

    @property
    def project_id(self):
        return self.client.session.get_project_id()

    @property
    def user_id(self):
        return self.client.session.get_user_id()


class V3ClientTestCase(ClientTestCase):
    version = '3'
