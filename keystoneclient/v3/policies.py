# Copyright 2011 OpenStack Foundation
# Copyright 2011 Nebula, Inc.
# All Rights Reserved.
#
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

from keystoneclient import base


class Policy(base.Resource):
    """Represents an Identity policy.

    Attributes:
        * id: a uuid that identifies the policy
        * blob: a policy document (blob)
        * type: the MIME type of the policy blob

    """

    def update(self, blob=None, type=None):
        kwargs = {
            'blob': blob if blob is not None else self.blob,
            'type': type if type is not None else self.type,
        }

        try:
            retval = self.manager.update(self.id, **kwargs)
            self = retval
        except Exception:
            retval = None

        return retval


class PolicyManager(base.CrudManager):
    """Manager class for manipulating Identity policies."""

    resource_class = Policy
    collection_key = 'policies'
    key = 'policy'

    def create(self, blob, type='application/json', **kwargs):
        """Create a policy.

        :param str blob: the policy document.
        :param str type: the MIME type of the policy blob.
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the created policy returned from server.
        :rtype: :class:`keystoneclient.v3.policies.Policy`

        """
        return super(PolicyManager, self).create(
            blob=blob,
            type=type,
            **kwargs)

    def get(self, policy):
        """Retrieve a policy.

        :param policy: the policy to be retrieved from the server.
        :type policy: str or :class:`keystoneclient.v3.policies.Policy`

        :returns: the specified policy returned from server.
        :rtype: :class:`keystoneclient.v3.policies.Policy`

        """
        return super(PolicyManager, self).get(
            policy_id=base.getid(policy))

    def list(self, **kwargs):
        """List policies.

        :param kwargs: allows filter criteria to be passed where
                       supported by the server.

        :returns: a list of policies.
        :rtype: list of :class:`keystoneclient.v3.policies.Policy`.

        """
        return super(PolicyManager, self).list(**kwargs)

    def update(self, policy, blob=None, type=None, **kwargs):
        """Update a policy.

        :param policy: the policy to be updated on the server.
        :type policy: str or :class:`keystoneclient.v3.policies.Policy`
        :param str blob: the new policy document.
        :param str type: the new MIME type of the policy blob.
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the updated policy returned from server.
        :rtype: :class:`keystoneclient.v3.policies.Policy`

        """
        return super(PolicyManager, self).update(
            policy_id=base.getid(policy),
            blob=blob,
            type=type,
            **kwargs)

    def delete(self, policy):
        """"Delete a policy.

        :param policy: the policy to be deleted on the server.
        :type policy: str or :class:`keystoneclient.v3.policies.Policy`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        return super(PolicyManager, self).delete(
            policy_id=base.getid(policy))
