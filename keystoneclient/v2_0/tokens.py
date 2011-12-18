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

    def authenticate(self, user_name=None, user_id=None, tenant_id=None,
                     tenant_name=None, password=None, token=None, return_raw=False):
        if token and token != password:
            params = {"auth": {"token": {"id": token}}}
        elif user_name and password:
            params = {"auth": {"passwordCredentials": {"username": user_name,
                                                       "password": password}}}
        elif user_id and password:
            params = {"auth": {"passwordCredentials": {"userId": user_id,
                                                       "password": password}}}
        else:
            raise ValueError('A username and password or token is required.')
        if tenant_id:
            params['auth']['tenantId'] = tenant_id
        elif tenant_name:
            params['auth']['tenantName'] = tenant_name
        return self._create('/tokens', params, "access", return_raw=return_raw)

    def endpoints(self, token):
        return self._get("/tokens/%s/endpoints" % base.getid(token), "token")
