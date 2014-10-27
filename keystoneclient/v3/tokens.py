# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from keystoneclient import access
from keystoneclient import base


class TokenManager(object):
    """Manager class for manipulating Identity tokens."""

    def __init__(self, client):
        self._client = client

    def revoke_token(self, token):
        """Revoke a token.

        :param token: Token to be revoked. This can be an instance of
                      :py:class:`keystoneclient.access.AccessInfo` or a string
                      token_id.
        """

        if isinstance(token, access.AccessInfo):
            token_id = token.auth_token
        else:
            token_id = base.getid(token)
        headers = {'X-Subject-Token': token_id}
        return self._client.delete('/auth/tokens', headers=headers)
