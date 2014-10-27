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

from oslo.serialization import jsonutils

from keystoneclient import utils


class Adapter(object):
    """An instance of a session with local variables.

    A session is a global object that is shared around amongst many clients. It
    therefore contains state that is relevant to everyone. There is a lot of
    state such as the service type and region_name that are only relevant to a
    particular client that is using the session. An adapter provides a wrapper
    of client local data around the global session object.
    """

    @utils.positional()
    def __init__(self, session, service_type=None, service_name=None,
                 interface=None, region_name=None, endpoint_override=None,
                 version=None, auth=None, user_agent=None,
                 connect_retries=None):
        """Create a new adapter.

        :param Session session: The session object to wrap.
        :param str service_type: The default service_type for URL discovery.
        :param str service_name: The default service_name for URL discovery.
        :param str interface: The default interface for URL discovery.
        :param str region_name: The default region_name for URL discovery.
        :param str endpoint_override: Always use this endpoint URL for requests
                                      for this client.
        :param tuple version: The version that this API targets.
        :param auth.BaseAuthPlugin auth: An auth plugin to use instead of the
                                         session one.
        :param str user_agent: The User-Agent string to set.
        :param int connect_retries: the maximum number of retries that should
                                    be attempted for connection errors.
                                    Default None - use session default which
                                    is don't retry.
        """
        self.session = session
        self.service_type = service_type
        self.service_name = service_name
        self.interface = interface
        self.region_name = region_name
        self.endpoint_override = endpoint_override
        self.version = version
        self.user_agent = user_agent
        self.auth = auth
        self.connect_retries = connect_retries

    def _set_endpoint_filter_kwargs(self, kwargs):
        if self.service_type:
            kwargs.setdefault('service_type', self.service_type)
        if self.service_name:
            kwargs.setdefault('service_name', self.service_name)
        if self.interface:
            kwargs.setdefault('interface', self.interface)
        if self.region_name:
            kwargs.setdefault('region_name', self.region_name)
        if self.version:
            kwargs.setdefault('version', self.version)

    def request(self, url, method, **kwargs):
        endpoint_filter = kwargs.setdefault('endpoint_filter', {})
        self._set_endpoint_filter_kwargs(endpoint_filter)

        if self.endpoint_override:
            kwargs.setdefault('endpoint_override', self.endpoint_override)

        if self.auth:
            kwargs.setdefault('auth', self.auth)
        if self.user_agent:
            kwargs.setdefault('user_agent', self.user_agent)
        if self.connect_retries is not None:
            kwargs.setdefault('connect_retries', self.connect_retries)

        return self.session.request(url, method, **kwargs)

    def get_token(self, auth=None):
        """Return a token as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin
                     on the session. (optional)
        :type auth: :class:`keystoneclient.auth.base.BaseAuthPlugin`

        :raises AuthorizationFailure: if a new token fetch fails.

        :returns string: A valid token.
        """
        return self.session.get_token(auth or self.auth)

    def get_endpoint(self, auth=None, **kwargs):
        """Get an endpoint as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin on
                     the session. (optional)
        :type auth: :class:`keystoneclient.auth.base.BaseAuthPlugin`

        :raises MissingAuthPlugin: if a plugin is not available.

        :returns string: An endpoint if available or None.
        """
        self._set_endpoint_filter_kwargs(kwargs)
        return self.session.get_endpoint(auth or self.auth, **kwargs)

    def invalidate(self, auth=None):
        """Invalidate an authentication plugin."""
        return self.session.invalidate(auth or self.auth)

    def get(self, url, **kwargs):
        return self.request(url, 'GET', **kwargs)

    def head(self, url, **kwargs):
        return self.request(url, 'HEAD', **kwargs)

    def post(self, url, **kwargs):
        return self.request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self.request(url, 'PUT', **kwargs)

    def patch(self, url, **kwargs):
        return self.request(url, 'PATCH', **kwargs)

    def delete(self, url, **kwargs):
        return self.request(url, 'DELETE', **kwargs)


class LegacyJsonAdapter(Adapter):
    """Make something that looks like an old HTTPClient.

    A common case when using an adapter is that we want an interface similar to
    the HTTPClients of old which returned the body as JSON as well.

    You probably don't want this if you are starting from scratch.
    """

    def request(self, *args, **kwargs):
        headers = kwargs.setdefault('headers', {})
        headers.setdefault('Accept', 'application/json')

        try:
            kwargs['json'] = kwargs.pop('body')
        except KeyError:
            pass

        resp = super(LegacyJsonAdapter, self).request(*args, **kwargs)

        body = None
        if resp.text:
            try:
                body = jsonutils.loads(resp.text)
            except ValueError:
                pass

        return resp, body
