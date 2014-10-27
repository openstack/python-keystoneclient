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

from keystoneclient import auth
from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient import utils


class Token(base.Resource):
    def __repr__(self):
        return "<Token %s>" % self._info

    @property
    def id(self):
        return self._info['token']['id']

    @property
    def expires(self):
        return self._info['token']['expires']

    @property
    def tenant(self):
        return self._info['token'].get('tenant')


class TokenManager(base.Manager):
    resource_class = Token

    @utils.positional(enforcement=utils.positional.WARN)
    def authenticate(self, username=None, tenant_id=None, tenant_name=None,
                     password=None, token=None, return_raw=False):
        if token:
            params = {"auth": {"token": {"id": token}}}
        elif username and password:
            params = {"auth": {"passwordCredentials": {"username": username,
                                                       "password": password}}}
        else:
            raise ValueError('A username and password or token is required.')
        if tenant_id:
            params['auth']['tenantId'] = tenant_id
        elif tenant_name:
            params['auth']['tenantName'] = tenant_name

        args = ['/tokens', params, 'access']
        kwargs = {'return_raw': return_raw, 'log': False}

        # NOTE(jamielennox): try doing a regular admin query first. If there is
        # no endpoint that can satisfy the request (eg an unscoped token) then
        # issue it against the auth_url.
        try:
            token_ref = self._create(*args, **kwargs)
        except exceptions.EndpointNotFound:
            kwargs['endpoint_filter'] = {'interface': auth.AUTH_INTERFACE}
            token_ref = self._create(*args, **kwargs)

        return token_ref

    def delete(self, token):
        return self._delete("/tokens/%s" % base.getid(token))

    def endpoints(self, token):
        return self._get("/tokens/%s/endpoints" % base.getid(token), "token")
