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


SAML2_ENDPOINT = '/auth/OS-FEDERATION/saml2'


class SamlManager(base.Manager):
    """Manager class for creating SAML assertions."""

    def create_saml_assertion(self, service_provider, token_id):
        """Create a SAML assertion from a token.

        Equivalent Identity API call:
        POST /auth/OS-FEDERATION/saml2

        :param service_provider: Service Provider resource.
        :type service_provider: string
        :param token_id: Token to transform to SAML assertion.
        :type token_id: string

        :returns: SAML representation of token_id
        :rtype: string
        """

        body = {
            'auth': {
                'identity': {
                    'methods': ['token'],
                    'token': {
                        'id': token_id
                    }
                },
                'scope': {
                    'service_provider': {
                        'id': base.getid(service_provider)
                    }
                }
            }
        }

        headers = {'Content-Type': 'application/json'}
        resp, body = self.client.post(SAML2_ENDPOINT, json=body,
                                      headers=headers)
        return resp.text
