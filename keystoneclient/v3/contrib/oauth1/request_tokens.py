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


class RequestToken(base.Resource):
    def authorize(self, roles):
        self.manager.authorize(self, roles)


class RequestTokenManager(base.CrudManager):
    """Manager class for manipulating Identity OAuth Request Tokens."""
    resource_class = RequestToken

    def authorize(self, request_token, roles):
        request_id = base.getid(request_token)
        endpoint = '/OS-OAUTH1/authorize/%s' % (request_id)
        body = {'roles': [{'id': base.getid(r_id)} for r_id in roles]}
        return self._put(endpoint, body, "token")

    def create(self, consumer_key, consumer_secret, project):
        # sign the request using oauthlib
        endpoint = '/OS-OAUTH1/request_token'
        headers = {'requested_project_id': base.getid(project)}
        oauth_client = oauth1.Client(consumer_key,
                                     client_secret=consumer_secret,
                                     signature_method=oauth1.SIGNATURE_HMAC,
                                     callback_uri="oob")
        url = self.client.auth_url + endpoint
        url, headers, body = oauth_client.sign(url, http_method='POST',
                                               headers=headers)

        # actually send the request
        resp, body = self.client.post(endpoint, headers=headers)

        # returned format will be:
        # 'oauth_token=12345&oauth_token_secret=67890'
        # with 'oauth_expires_at' possibly there, too
        credentials = urlparse.parse_qs(body)
        key = credentials.get('oauth_token')[0]
        secret = credentials.get('oauth_token_secret')[0]
        request_token = {'request_key': key, 'id': key,
                         'request_secret': secret}

        if credentials.get('oauth_expires_at'):
            expires = credentials.get('oauth_expires_at')[0]
            request_token['expires'] = expires

        return self.resource_class(self, request_token)
