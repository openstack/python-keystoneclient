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

from oslo_config import cfg

from keystoneclient import access
from keystoneclient.auth.identity.v3 import federated


class OidcPassword(federated.FederatedBaseAuth):
    """Implement authentication plugin for OpenID Connect protocol.

    OIDC or OpenID Connect is a protocol for federated authentication.

    The OpenID Connect specification can be found at::
    ``http://openid.net/specs/openid-connect-core-1_0.html``
    """

    @classmethod
    def get_options(cls):
        options = super(OidcPassword, cls).get_options()
        options.extend([
            cfg.StrOpt('username', help='Username'),
            cfg.StrOpt('password', secret=True, help='Password'),
            cfg.StrOpt('client-id', help='OAuth 2.0 Client ID'),
            cfg.StrOpt('client-secret', secret=True,
                       help='OAuth 2.0 Client Secret'),
            cfg.StrOpt('access-token-endpoint',
                       help='OpenID Connect Provider Token Endpoint'),
            cfg.StrOpt('scope', default="profile",
                       help='OpenID Connect scope that is requested from OP')
        ])
        return options

    def __init__(self, auth_url, identity_provider, protocol,
                 username, password, client_id, client_secret,
                 access_token_endpoint, scope='profile',
                 grant_type='password'):
        """The OpenID Connect plugin.

        It expects the following:

        :param auth_url: URL of the Identity Service
        :type auth_url: string

        :param identity_provider: Name of the Identity Provider the client
                                  will authenticate against
        :type identity_provider: string

        :param protocol: Protocol name as configured in keystone
        :type protocol: string

        :param username: Username used to authenticate
        :type username: string

        :param password: Password used to authenticate
        :type password: string

        :param client_id: OAuth 2.0 Client ID
        :type client_id: string

        :param client_secret: OAuth 2.0 Client Secret
        :type client_secret: string

        :param access_token_endpoint: OpenID Connect Provider Token Endpoint,
                                      for example:
                                      https://localhost:8020/oidc/OP/token
        :type access_token_endpoint: string

        :param scope: OpenID Connect scope that is requested from OP,
                      defaults to "profile", for example: "profile email"
        :type scope: string

        :param grant_type: OpenID Connect grant type, it represents the flow
                           that is used to talk to the OP. Valid values are:
                           "authorization_code", "refresh_token", or
                           "password".
        :type grant_type: string
        """
        super(OidcPassword, self).__init__(auth_url, identity_provider,
                                           protocol)
        self._username = username
        self._password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token_endpoint = access_token_endpoint
        self.scope = scope
        self.grant_type = grant_type

    @property
    def username(self):
        # Override to remove deprecation.
        return self._username

    @username.setter
    def username(self, value):
        # Override to remove deprecation.
        self._username = value

    @property
    def password(self):
        # Override to remove deprecation.
        return self._password

    @password.setter
    def password(self, value):
        # Override to remove deprecation.
        self._password = value

    def get_unscoped_auth_ref(self, session):
        """Authenticate with OpenID Connect and get back claims.

        This is a multi-step process. First an access token must be retrieved,
        to do this, the username and password, the OpenID Connect client ID
        and secret, and the access token endpoint must be known.

        Secondly, we then exchange the access token upon accessing the
        protected Keystone endpoint (federated auth URL). This will trigger
        the OpenID Connect Provider to perform a user introspection and
        retrieve information (specified in the scope) about the user in
        the form of an OpenID Connect Claim. These claims will be sent
        to Keystone in the form of environment variables.

        :param session: a session object to send out HTTP requests.
        :type session: keystoneclient.session.Session

        :returns: a token data representation
        :rtype: :py:class:`keystoneclient.access.AccessInfo`
        """
        # get an access token
        client_auth = (self.client_id, self.client_secret)
        payload = {'grant_type': self.grant_type, 'username': self.username,
                   'password': self.password, 'scope': self.scope}
        response = self._get_access_token(session, client_auth, payload,
                                          self.access_token_endpoint)
        access_token = response.json()['access_token']

        # use access token against protected URL
        headers = {'Authorization': 'Bearer ' + access_token}
        response = self._get_keystone_token(session, headers,
                                            self.federated_token_url)

        # grab the unscoped token
        token = response.headers['X-Subject-Token']
        token_json = response.json()['token']
        return access.AccessInfoV3(token, **token_json)

    def _get_access_token(self, session, client_auth, payload,
                          access_token_endpoint):
        """Exchange a variety of user supplied values for an access token.

        :param session: a session object to send out HTTP requests.
        :type session: keystoneclient.session.Session

        :param client_auth: a tuple representing client id and secret
        :type client_auth: tuple

        :param payload: a dict containing various OpenID Connect values, for
                        example::
                          {'grant_type': 'password', 'username': self.username,
                           'password': self.password, 'scope': self.scope}
        :type payload: dict

        :param access_token_endpoint: URL to use to get an access token, for
                                      example: https://localhost/oidc/token
        :type access_token_endpoint: string
        """
        op_response = session.post(self.access_token_endpoint,
                                   requests_auth=client_auth,
                                   data=payload,
                                   authenticated=False)
        return op_response

    def _get_keystone_token(self, session, headers, federated_token_url):
        r"""Exchange an acess token for a keystone token.

        By Sending the access token in an `Authorization: Bearer` header, to
        an OpenID Connect protected endpoint (Federated Token URL). The
        OpenID Connect server will use the access token to look up information
        about the authenticated user (this technique is called instrospection).
        The output of the instrospection will be an OpenID Connect Claim, that
        will be used against the mapping engine. Should the mapping engine
        succeed, a Keystone token will be presented to the user.

        :param session: a session object to send out HTTP requests.
        :type session: keystoneclient.session.Session

        :param headers: an Authorization header containing the access token.
        :type headers_: dict

        :param federated_auth_url: Protected URL for federated authentication,
                                   for example: https://localhost:5000/v3/\
                                   OS-FEDERATION/identity_providers/bluepages/\
                                   protocols/oidc/auth
        :type federated_auth_url: string
        """
        auth_response = session.post(self.federated_token_url,
                                     headers=headers,
                                     authenticated=False)
        return auth_response
