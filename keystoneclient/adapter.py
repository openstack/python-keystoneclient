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

from keystoneclient.openstack.common import jsonutils
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
                 interface=None, region_name=None, auth=None,
                 user_agent=None):
        """Create a new adapter.

        :param Session session: The session object to wrap.
        :param str service_type: The default service_type for URL discovery.
        :param str service_name: The default service_name for URL discovery.
        :param str interface: The default interface for URL discovery.
        :param str region_name: The default region_name for URL discovery.
        :param auth.BaseAuthPlugin auth: An auth plugin to use instead of the
                                         session one.
        :param str user_agent: The User-Agent string to set.
        """

        self.session = session
        self.service_type = service_type
        self.service_name = service_name
        self.interface = interface
        self.region_name = region_name
        self.user_agent = user_agent
        self.auth = auth

    def request(self, url, method, **kwargs):
        endpoint_filter = kwargs.setdefault('endpoint_filter', {})

        if self.service_type:
            endpoint_filter.setdefault('service_type', self.service_type)
        if self.service_name:
            endpoint_filter.setdefault('service_name', self.service_name)
        if self.interface:
            endpoint_filter.setdefault('interface', self.interface)
        if self.region_name:
            endpoint_filter.setdefault('region_name', self.region_name)

        if self.auth:
            kwargs.setdefault('auth', self.auth)
        if self.user_agent:
            kwargs.setdefault('user_agent', self.user_agent)

        return self.session.request(url, method, **kwargs)

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
