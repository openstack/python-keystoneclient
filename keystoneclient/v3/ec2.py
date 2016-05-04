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

from keystoneclient import base


class EC2(base.Resource):

    def __repr__(self):
        """Return string representation of EC2 resource information."""
        return "<EC2 %s>" % self._info


class EC2Manager(base.ManagerWithFind):

    resource_class = EC2

    def create(self, user_id, project_id):
        """Create a new access/secret pair for the user/project pair.

        :rtype: object of type :class:`EC2`
        """
        # NOTE(jamielennox): Yes, this uses tenant_id as a key even though we
        # are in the v3 API.
        return self._post('/users/%s/credentials/OS-EC2' % user_id,
                          body={'tenant_id': project_id},
                          response_key="credential")

    def list(self, user_id):
        """Get a list of access/secret pairs for a user_id.

        :rtype: list of :class:`EC2`
        """
        return self._list("/users/%s/credentials/OS-EC2" % user_id,
                          response_key="credentials")

    def get(self, user_id, access):
        """Get the access/secret pair for a given access key.

        :rtype: object of type :class:`EC2`
        """
        url = "/users/%s/credentials/OS-EC2/%s" % (user_id, base.getid(access))
        return self._get(url, response_key="credential")

    def delete(self, user_id, access):
        """Delete an access/secret pair for a user."""
        return self._delete("/users/%s/credentials/OS-EC2/%s" %
                            (user_id, base.getid(access)))
