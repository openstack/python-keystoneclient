from keystoneclient import base

class Token(base.Resource):
    def __repr__(self):
        return "<Token %s>" % self._info

    @property
    def id(self):
        return self._info['token']['id']

    @property
    def username(self):
        return self._info['user'].get('username', None)

    @property
    def tenant_id(self):
        return self._info['user'].get('tenantId', None)


class TokenManager(base.ManagerWithFind):
    resource_class = Token

    def authenticate(self, username=None, password=None, tenant=None,
                        token=None, return_raw=False):
        if token and token != password:
            params = {"auth": {"token": {"id": token}}}
        elif username and password:
            params = {"auth": {"passwordCredentials": {"username": username,
                                                       "password": password}}}
        else:
            raise ValueError('A username and password or token is required.')
        if tenant:
            params['auth']['tenantId'] = tenant
        return self._create('/tokens', params, "access", return_raw=return_raw)

    def endpoints(self, token):
        return self._get("/tokens/%s/endpoints" % base.getid(token), "token")
