# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import abc

import six

from keystoneclient import access
from keystoneclient.auth.identity import base
from keystoneclient import exceptions
from keystoneclient import utils


@six.add_metaclass(abc.ABCMeta)
class Auth(base.BaseIdentityPlugin):

    @staticmethod
    def _factory(auth_url, **kwargs):
        """Construct a plugin appropriate to your available arguments.

        This function should only be used for loading authentication from a
        config file or other source where you do not know the type of plugin
        that is required.

        If you know the style of authorization you require then you should
        construct that plugin directly.

        :raises NoMatchingPlugin: if a plugin cannot be constructed.

        return Auth: a plugin that can be passed to a session.
        """
        username = kwargs.pop('username', None)
        password = kwargs.pop('password', None)
        token = kwargs.pop('token', None)

        if token:
            return Token(auth_url, token, **kwargs)
        elif username and password:
            return Password(auth_url, username, password, **kwargs)

        msg = 'A username and password or token is required.'
        raise exceptions.NoMatchingPlugin(msg)

    @utils.positional()
    def __init__(self, auth_url,
                 trust_id=None,
                 tenant_id=None,
                 tenant_name=None):
        """Construct an Identity V2 Authentication Plugin.

        :param string auth_url: Identity service endpoint for authorization.
        :param string trust_id: Trust ID for trust scoping.
        :param string tenant_id: Tenant ID for project scoping.
        :param string tenant_name: Tenant name for project scoping.
        """
        super(Auth, self).__init__(auth_url=auth_url)

        self.trust_id = trust_id
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name

    def get_auth_ref(self, session, **kwargs):
        headers = {}
        url = self.auth_url + '/tokens'
        params = {'auth': self.get_auth_data(headers)}

        if self.tenant_id:
            params['auth']['tenantId'] = self.tenant_id
        elif self.tenant_name:
            params['auth']['tenantName'] = self.tenant_name
        if self.trust_id:
            params['auth']['trust_id'] = self.trust_id

        resp = session.post(url, json=params, headers=headers,
                            authenticated=False)
        return access.AccessInfoV2(**resp.json()['access'])

    @abc.abstractmethod
    def get_auth_data(self, headers=None):
        """Return the authentication section of an auth plugin.

        :param dict headers: The headers that will be sent with the auth
                             request if a plugin needs to add to them.
        :return dict: A dict of authentication data for the auth type.
        """


class Password(Auth):

    def __init__(self, auth_url, username, password, **kwargs):
        """A plugin for authenticating with a username and password.

        :param string auth_url: Identity service endpoint for authorization.
        :param string username: Username for authentication.
        :param string password: Password for authentication.
        """
        super(Password, self).__init__(auth_url, **kwargs)
        self.username = username
        self.password = password

    def get_auth_data(self, headers=None):
        return {'passwordCredentials': {'username': self.username,
                                        'password': self.password}}


class Token(Auth):

    def __init__(self, auth_url, token, **kwargs):
        """A plugin for authenticating with an existing token.

        :param string auth_url: Identity service endpoint for authorization.
        :param string token: Existing token for authentication.
        """
        super(Token, self).__init__(auth_url, **kwargs)
        self.token = token

    def get_auth_data(self, headers=None):
        if headers is not None:
            headers['X-Auth-Token'] = self.token
        return {'token': {'id': self.token}}
