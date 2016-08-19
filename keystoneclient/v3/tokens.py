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

from positional import positional

from keystoneclient import access
from keystoneclient import base


def _calc_id(token):
    if isinstance(token, access.AccessInfo):
        return token.auth_token

    return base.getid(token)


class TokenManager(object):
    """Manager class for manipulating Identity tokens."""

    def __init__(self, client):
        self._client = client

    def revoke_token(self, token):
        """Revoke a token.

        :param token: The token to be revoked.
        :type token: str or :class:`keystoneclient.access.AccessInfo`

        """
        token_id = _calc_id(token)
        headers = {'X-Subject-Token': token_id}
        return self._client.delete('/auth/tokens', headers=headers)

    @positional.method(0)
    def get_revoked(self, audit_id_only=False):
        """Get revoked tokens list.

        :param bool audit_id_only: If true, the server is requested to not send
                                   token IDs, but only audit IDs instead.
                                   **New in version 2.2.0.**
        :returns: A dict containing ``signed`` which is a CMS formatted string
                  if the server signed the response. If `audit_id_only` is true
                  then the response may be a dict containing ``revoked`` which
                  is the list of token audit IDs and expiration times.
        :rtype: dict

        """
        path = '/auth/tokens/OS-PKI/revoked'
        if audit_id_only:
            path += '?audit_id_only'
        resp, body = self._client.get(path)
        return body

    @positional.method(1)
    def get_token_data(self, token, include_catalog=True):
        """Fetch the data about a token from the identity server.

        :param str token: The ID of the token to be fetched.
        :param bool include_catalog: Whether the service catalog should be
                                     included in the response.

        :rtype: dict

        """
        headers = {'X-Subject-Token': token}

        url = '/auth/tokens'
        if not include_catalog:
            url += '?nocatalog'

        resp, body = self._client.get(url, headers=headers)
        return body

    @positional.method(1)
    def validate(self, token, include_catalog=True):
        """Validate a token.

        :param token: The token to be validated.
        :type token: str or :class:`keystoneclient.access.AccessInfo`
        :param include_catalog: If False, the response is requested to not
                                include the catalog.

        :rtype: :class:`keystoneclient.access.AccessInfoV3`

        """
        token_id = _calc_id(token)
        body = self.get_token_data(token_id, include_catalog=include_catalog)
        return access.AccessInfo.factory(auth_token=token_id, body=body)
