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
from positional import positional

from keystoneclient.auth.identity.generic import password
from keystoneclient import exceptions as exc
from keystoneclient.i18n import _


class DefaultCLI(password.Password):
    """A Plugin that provides typical authentication options for CLIs.

    This plugin provides standard username and password authentication options
    as well as allowing users to override with a custom token and endpoint.
    """

    @positional()
    def __init__(self, endpoint=None, token=None, **kwargs):
        super(DefaultCLI, self).__init__(**kwargs)

        self._token = token
        self._endpoint = endpoint

    @classmethod
    def get_options(cls):
        options = super(DefaultCLI, cls).get_options()
        options.extend([cfg.StrOpt('endpoint',
                                   help='A URL to use instead of a catalog'),
                        cfg.StrOpt('token',
                                   secret=True,
                                   help='Always use the specified token')])
        return options

    def get_token(self, *args, **kwargs):
        if self._token:
            return self._token

        return super(DefaultCLI, self).get_token(*args, **kwargs)

    def get_endpoint(self, *args, **kwargs):
        if self._endpoint:
            return self._endpoint

        return super(DefaultCLI, self).get_endpoint(*args, **kwargs)

    @classmethod
    def load_from_argparse_arguments(cls, namespace, **kwargs):
        token = kwargs.get('token') or namespace.os_token
        endpoint = kwargs.get('endpoint') or namespace.os_endpoint
        auth_url = kwargs.get('auth_url') or namespace.os_auth_url

        if token and not endpoint:
            # if a user provides a token then they must also provide an
            # endpoint because we aren't fetching a token to get a catalog from
            msg = _('A service URL must be provided with a token')
            raise exc.CommandError(msg)
        elif (not token) and (not auth_url):
            # if you don't provide a token you are going to provide at least an
            # auth_url with which to authenticate.
            raise exc.CommandError(_('Expecting an auth URL via either '
                                     '--os-auth-url or env[OS_AUTH_URL]'))

        plugin = super(DefaultCLI, cls).load_from_argparse_arguments(namespace,
                                                                     **kwargs)

        if (not token) and (not plugin._password):
            # we do this after the load so that the base plugin has an
            # opportunity to prompt the user for a password
            raise exc.CommandError(_('Expecting a password provided via '
                                     'either --os-password, env[OS_PASSWORD], '
                                     'or prompted response'))

        return plugin
