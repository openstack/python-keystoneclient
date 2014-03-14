# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

import oauthlib.oauth1 as oauth1
from six.moves.urllib import parse as urlparse

from keystoneclient import base


class AccessToken(base.Resource):
    pass


class AccessTokenManager(base.CrudManager):
    """Manager class for manipulating Identity OAuth Access Tokens."""
    resource_class = AccessToken

    def create(self, consumer_key, consumer_secret, request_key,
               request_secret, verifier):
        # sign the request using oauthlib
        endpoint = '/OS-OAUTH1/access_token'
        oauth_client = oauth1.Client(consumer_key,
                                     client_secret=consumer_secret,
                                     resource_owner_key=request_key,
                                     resource_owner_secret=request_secret,
                                     signature_method=oauth1.SIGNATURE_HMAC,
                                     verifier=verifier)
        url = self.client.auth_url + endpoint
        url, headers, body = oauth_client.sign(url, http_method='POST')

        # actually send the request
        resp, body = self.client.post(endpoint, headers=headers)

        # returned format will be:
        # 'oauth_token=12345&oauth_token_secret=67890'
        # with 'oauth_expires_at' possibly there, too
        credentials = urlparse.parse_qs(body)
        key = credentials['oauth_token'][0]
        secret = credentials['oauth_token_secret'][0]
        access_token = {'access_key': key, 'id': key,
                        'access_secret': secret}

        if credentials.get('oauth_expires_at'):
            expires = credentials['oauth_expires_at'][0]
            access_token['expires'] = expires

        return self.resource_class(self, access_token)
