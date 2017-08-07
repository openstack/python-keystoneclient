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

    def get_token_data(self, token, include_catalog=True, allow_expired=False):
        """Fetch the data about a token from the identity server.

        :param str token: The ID of the token to be fetched.
        :param bool include_catalog: Whether the service catalog should be
                                     included in the response.
        :param allow_expired: If True the token will be validated and returned
                              if it has already expired.

        :rtype: dict

        """
        headers = {'X-Subject-Token': token}
        flags = []

        url = '/auth/tokens'

        if not include_catalog:
            flags.append('nocatalog')
        if allow_expired:
            flags.append('allow_expired=1')

        if flags:
            url = '%s?%s' % (url, '&'.join(flags))

        resp, body = self._client.get(url, headers=headers)
        return body

    def validate(self, token, include_catalog=True, allow_expired=False):
        """Validate a token.

        :param token: The token to be validated.
        :type token: str or :class:`keystoneclient.access.AccessInfo`
        :param include_catalog: If False, the response is requested to not
                                include the catalog.
        :param allow_expired: If True the token will be validated and returned
                              if it has already expired.
        :type allow_expired: bool

        :rtype: :class:`keystoneclient.access.AccessInfoV3`

        """
        token_id = _calc_id(token)
        body = self.get_token_data(token_id,
                                   include_catalog=include_catalog,
                                   allow_expired=allow_expired)
        return access.AccessInfo.factory(auth_token=token_id, body=body)
