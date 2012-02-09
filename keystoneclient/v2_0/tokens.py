from keystoneclient import base


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
        return self._info['token'].get('tenant', None)


class TokenManager(base.ManagerWithFind):
    resource_class = Token

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
        return self._create('/tokens', params, "access", return_raw=return_raw)

    def delete(self, token):
        return self._delete("/tokens/%s" % base.getid(token))

    def endpoints(self, token):
        return self._get("/tokens/%s/endpoints" % base.getid(token), "token")
