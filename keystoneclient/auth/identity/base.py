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
import logging
import six

from keystoneclient.auth import base

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseIdentityPlugin(base.BaseAuthPlugin):

    # we count a token as valid if it is valid for at least this many seconds
    MIN_TOKEN_LIFE_SECONDS = 1

    def __init__(self,
                 auth_url=None,
                 username=None,
                 password=None,
                 token=None,
                 trust_id=None):

        super(BaseIdentityPlugin, self).__init__()

        self.auth_url = auth_url
        self.auth_ref = None

        # NOTE(jamielennox): DEPRECATED. The following should not really be set
        # here but handled by the individual auth plugin.
        self.username = username
        self.password = password
        self.token = token
        self.trust_id = trust_id

    @abc.abstractmethod
    def get_auth_ref(self, session, **kwargs):
        """Obtain a token from an OpenStack Identity Service.

        This method is overridden by the various token version plugins.

        This function should not be called independently and is expected to be
        invoked via the do_authenticate function.

        This function will be invoked if the AcessInfo object cached by the
        plugin is not valid. Thus plugins should always fetch a new AccessInfo
        when invoked. If you are looking to just retrieve the current auth
        data then you should use get_access.

        :raises InvalidResponse: The response returned wasn't appropriate.
        :raises HttpError: An error from an invalid HTTP response.

        :returns AccessInfo: Token access information.
        """

    def get_token(self, session, **kwargs):
        """Return a valid auth token.

        If a valid token is not present then a new one will be fetched.

        :raises HttpError: An error from an invalid HTTP response.

        :return string: A valid token.
        """
        return self.get_access(session).auth_token

    def get_access(self, session, **kwargs):
        """Fetch or return a current AccessInfo object.

        If a valid AccessInfo is present then it is returned otherwise a new
        one will be fetched.

        :raises HttpError: An error from an invalid HTTP response.

        :returns AccessInfo: Valid AccessInfo
        """
        if (not self.auth_ref or
                self.auth_ref.will_expire_soon(self.MIN_TOKEN_LIFE_SECONDS)):
            self.auth_ref = self.get_auth_ref(session)

        return self.auth_ref

    def get_endpoint(self, session, service_type=None, interface=None,
                     region_name=None, **kwargs):
        """Return a valid endpoint for a service.

        If a valid token is not present then a new one will be fetched using
        the session and kwargs.

        :param string service_type: The type of service to lookup the endpoint
                                    for. This plugin will return None (failure)
                                    if service_type is not provided.
        :param string interface: The exposure of the endpoint. Should be
                                 `public`, `internal` or `admin`.
                                 Defaults to `public`.
        :param string region_name: The region the endpoint should exist in.
                                   (optional)

        :raises HttpError: An error from an invalid HTTP response.

        :return string or None: A valid endpoint URL or None if not available.
        """
        if not service_type:
            LOG.warn('Plugin cannot return an endpoint without knowing the '
                     'service type that is required. Add service_type to '
                     'endpoint filtering data.')
            return None

        if not interface:
            interface = 'public'

        service_catalog = self.get_access(session).service_catalog
        return service_catalog.url_for(service_type=service_type,
                                       endpoint_type=interface,
                                       region_name=region_name)
