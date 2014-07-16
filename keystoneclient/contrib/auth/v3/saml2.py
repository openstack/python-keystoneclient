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

from lxml import etree
from oslo.config import cfg

from keystoneclient import access
from keystoneclient.auth.identity import v3
from keystoneclient import exceptions


class Saml2UnscopedTokenAuthMethod(v3.AuthMethod):
    _method_parameters = []

    def get_auth_data(self, session, auth, headers, **kwargs):
        raise exceptions.MethodNotImplemented(('This method should never '
                                              'be called'))


class Saml2UnscopedToken(v3.AuthConstructor):
    """Implement authentication plugin for SAML2 protocol.

    ECP stands for ``Enhanced Client or Proxy`` and is a SAML2 extension
    for federated authentication where a transportation layer consists of
    HTTP protocol and XML SOAP messages.

    Read for more information::
    ``https://wiki.shibboleth.net/confluence/display/SHIB2/ECP``

    The SAML2 ECP specification can be found at::
    ``https://www.oasis-open.org/committees/download.php/
    49979/saml-ecp-v2.0-wd09.pdf``

    Currently only HTTPBasicAuth mechanism is available for the IdP
    authenication.

    """

    _auth_method_class = Saml2UnscopedTokenAuthMethod

    PROTOCOL = 'saml2'
    HTTP_MOVED_TEMPORARILY = 302
    SAML2_HEADER_INDEX = 0
    ECP_SP_EMPTY_REQUEST_HEADERS = {
        'Accept': 'text/html; application/vnd.paos+xml',
        'PAOS': ('ver="urn:liberty:paos:2003-08";"urn:oasis:names:tc:'
                 'SAML:2.0:profiles:SSO:ecp"')
    }

    ECP_SP_SAML2_REQUEST_HEADERS = {
        'Content-Type': 'application/vnd.paos+xml'
    }

    ECP_SAML2_NAMESPACES = {
        'ecp': 'urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp',
        'S': 'http://schemas.xmlsoap.org/soap/envelope/',
        'paos': 'urn:liberty:paos:2003-08'
    }

    ECP_RELAY_STATE = '//ecp:RelayState'

    ECP_SERVICE_PROVIDER_CONSUMER_URL = ('/S:Envelope/S:Header/paos:Request/'
                                         '@responseConsumerURL')

    ECP_IDP_CONSUMER_URL = ('/S:Envelope/S:Header/ecp:Response/'
                            '@AssertionConsumerServiceURL')

    SOAP_FAULT = """
    <S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
       <S:Body>
         <S:Fault>
            <faultcode>S:Server</faultcode>
            <faultstring>responseConsumerURL from SP and
            assertionConsumerServiceURL from IdP do not match
            </faultstring>
         </S:Fault>
       </S:Body>
    </S:Envelope>
    """

    def __init__(self, auth_url,
                 identity_provider,
                 identity_provider_url,
                 username, password,
                 **kwargs):
        """Class constructor accepting following parameters:
        :param auth_url: URL of the Identity Service
        :type auth_url: string

        :param identity_provider: name of the Identity Provider the client
                                  will authenticate against. This parameter
                                  will be used to build a dynamic URL used to
                                  obtain unscoped OpenStack token.
        :type identity_provider: string

        :param identity_provider_url: An Identity Provider URL, where the SAML2
                                      authn request will be sent.
        :type identity_provider_url: string

        :param username: User's login
        :type username: string

        :param password: User's password
        :type password: string

        """
        super(Saml2UnscopedToken, self).__init__(auth_url=auth_url, **kwargs)
        self.identity_provider = identity_provider
        self.identity_provider_url = identity_provider_url
        self.username, self.password = username, password

    @classmethod
    def get_options(cls):
        options = super(Saml2UnscopedToken, cls).get_options()
        options.extend([
            cfg.StrOpt('identity-provider', help="Identity Provider's name"),
            cfg.StrOpt('identity-provider-url',
                       help="Identity Provider's URL"),
            cfg.StrOpt('user-name', dest='username', help='Username',
                       deprecated_name='username'),
            cfg.StrOpt('password', help='Password')
        ])
        return options

    def _handle_http_302_ecp_redirect(self, session, response, method,
                                      **kwargs):
        if response.status_code != self.HTTP_MOVED_TEMPORARILY:
            return response

        location = response.headers['location']
        return session.request(location, method, **kwargs)

    def _first(self, _list):
        if len(_list) != 1:
            raise IndexError("Only single element list can be flatten")
        return _list[0]

    def _prepare_idp_saml2_request(self, saml2_authn_request):
        header = saml2_authn_request[self.SAML2_HEADER_INDEX]
        saml2_authn_request.remove(header)

    def _check_consumer_urls(self, session, sp_response_consumer_url,
                             idp_sp_response_consumer_url):
        """Check if consumer URLs issued by SP and IdP are equal.

        In the initial SAML2 authn Request issued by a Service Provider
        there is a url called ``consumer url``. A trusted Identity Provider
        should issue identical url. If the URLs are not equal the federated
        authn process should be interrupted and the user should be warned.

        :param session: session object to send out HTTP requests.
        :type session: keystoneclient.session.Session
        :param sp_response_consumer_url: consumer URL issued by a SP
        :type  sp_response_consumer_url: string
        :param idp_sp_response_consumer_url: consumer URL issued by an IdP
        :type idp_sp_response_consumer_url: string

        """
        if sp_response_consumer_url != idp_sp_response_consumer_url:
            # send fault message to the SP, discard the response
            session.post(sp_response_consumer_url, data=self.SOAP_FAULT,
                         headers=self.ECP_SP_SAML2_REQUEST_HEADERS,
                         authenticated=False)

            # prepare error message and raise an exception.
            msg = ("Consumer URLs from Service Provider %(service_provider)s "
                   "%(sp_consumer_url)s and Identity Provider "
                   "%(identity_provider)s %(idp_consumer_url)s are not equal")
            msg = msg % {
                'service_provider': self.saml2_token_url,
                'sp_consumer_url': sp_response_consumer_url,
                'identity_provider': self.identity_provider,
                'idp_consumer_url': idp_sp_response_consumer_url
            }

            raise exceptions.ValidationError(msg)

    def _send_service_provider_request(self, session):
        """Initial HTTP GET request to the SAML2 protected endpoint.

        It's crucial to include HTTP headers indicating that the client is
        willing to take advantage of the ECP SAML2 extension and receive data
        as the SOAP.
        Unlike standard authentication methods in the OpenStack Identity,
        the client accesses::
        ``/v3/OS-FEDERATION/identity_providers/{identity_providers}/
        protocols/{protocol}/auth``

        After a successful HTTP call the HTTP response should include SAML2
        authn request in the XML format.

        If a HTTP response contains ``X-Subject-Token`` in the headers and
        the response body is a valid JSON assume the user was already
        authenticated and Keystone returned a valid unscoped token.
        Return True indicating the user was already authenticated.

        :param session: a session object to send out HTTP requests.
        :type session: keystoneclient.session.Session

        """
        sp_response = session.get(self.saml2_token_url,
                                  headers=self.ECP_SP_EMPTY_REQUEST_HEADERS,
                                  authenticated=False)

        if 'X-Subject-Token' in sp_response.headers:
            self.authenticated_response = sp_response
            return True

        try:
            self.saml2_authn_request = etree.XML(sp_response.content)
        except etree.XMLSyntaxError as e:
            msg = ("SAML2: Error parsing XML returned "
                   "from Service Provider, reason: %s" % e)
            raise exceptions.AuthorizationFailure(msg)

        relay_state = self.saml2_authn_request.xpath(
            self.ECP_RELAY_STATE, namespaces=self.ECP_SAML2_NAMESPACES)
        self.relay_state = self._first(relay_state)

        sp_response_consumer_url = self.saml2_authn_request.xpath(
            self.ECP_SERVICE_PROVIDER_CONSUMER_URL,
            namespaces=self.ECP_SAML2_NAMESPACES)
        self.sp_response_consumer_url = self._first(
            sp_response_consumer_url)
        return False

    def _send_idp_saml2_authn_request(self, session):
        """Present modified SAML2 authn assertion from the Service Provider."""

        self._prepare_idp_saml2_request(self.saml2_authn_request)
        idp_saml2_authn_request = self.saml2_authn_request

        # Currently HTTPBasicAuth method is hardcoded into the plugin
        idp_response = session.post(
            self.identity_provider_url,
            headers={'Content-type': 'text/xml'},
            data=etree.tostring(idp_saml2_authn_request),
            requests_auth=(self.username, self.password))

        try:
            self.saml2_idp_authn_response = etree.XML(idp_response.content)
        except etree.XMLSyntaxError as e:
            msg = ("SAML2: Error parsing XML returned "
                   "from Identity Provider, reason: %s" % e)
            raise exceptions.AuthorizationFailure(msg)

        idp_response_consumer_url = self.saml2_idp_authn_response.xpath(
            self.ECP_IDP_CONSUMER_URL,
            namespaces=self.ECP_SAML2_NAMESPACES)

        self.idp_response_consumer_url = self._first(
            idp_response_consumer_url)

        self._check_consumer_urls(session, self.idp_response_consumer_url,
                                  self.sp_response_consumer_url)

    def _send_service_provider_saml2_authn_response(self, session):
        """Present SAML2 assertion to the Service Provider.

        The assertion is issued by a trusted Identity Provider for the
        authenticated user. This function directs the HTTP request to SP
        managed URL, for instance: ``https://<host>:<port>/Shibboleth.sso/
        SAML2/ECP``.
        Upon success the there's a session created and access to the protected
        resource is granted. Many implementations of the SP return HTTP 302
        status code pointing to the protected URL (``https://<host>:<port>/v3/
        OS-FEDERATION/identity_providers/{identity_provider}/protocols/
        {protocol_id}/auth`` in this case). Saml2 plugin should point to that
        URL again, with HTTP GET method, expecting an unscoped token.

        :param session: a session object to send out HTTP requests.

        """
        self.saml2_idp_authn_response[0][0] = self.relay_state

        response = session.post(
            self.idp_response_consumer_url,
            headers=self.ECP_SP_SAML2_REQUEST_HEADERS,
            data=etree.tostring(self.saml2_idp_authn_response),
            authenticated=False, redirect=False)

        # Don't follow HTTP specs - after the HTTP 302 response don't repeat
        # the call directed to the Location URL. In this case, this is an
        # indication that saml2 session is now active and protected resource
        # can be accessed.
        response = self._handle_http_302_ecp_redirect(
            session, response, method='GET',
            headers=self.ECP_SP_SAML2_REQUEST_HEADERS)

        self.authenticated_response = response

    @property
    def saml2_token_url(self):
        """Return full URL where authorization data is sent."""
        values = {
            'host': self.auth_url.rstrip('/'),
            'identity_provider': self.identity_provider,
            'protocol': self.PROTOCOL
        }
        url = ("%(host)s/OS-FEDERATION/identity_providers/"
               "%(identity_provider)s/protocols/%(protocol)s/auth")
        url = url % values

        return url

    def _get_unscoped_token(self, session, **kwargs):
        """Get unscoped OpenStack token after federated authentication.

        This is a multi-step process including multiple HTTP requests.

        The federated authentication consists of::
        * HTTP GET request to the Identity Service (acting as a Service
          Provider). Client utilizes URL::
          ``/v3/OS-FEDERATION/identity_providers/{identity_provider}/
          protocols/saml2/auth``.
          It's crucial to include HTTP headers indicating we are expecting
          SOAP message in return.
          Service Provider should respond with such SOAP message.
          This step is handed by a method
          ``Saml2UnscopedToken_send_service_provider_request()``

        * HTTP POST request to the external Identity Provider service with
          ECP extension enabled. The content sent is a header removed SOAP
          message  returned from the Service Provider. It's also worth noting
          that ECP extension to the SAML2 doesn't define authentication method.
          The most popular is HttpBasicAuth with just user and password.
          Other possibilities could be X509 certificates or Kerberos.
          Upon successful authentication the user should receive a SAML2
          assertion.
          This step is handed by a method
          ``Saml2UnscopedToken_send_idp_saml2_authn_request(session)``

        * HTTP POST request again to the Service Provider. The body of the
          request includes SAML2 assertion issued by a trusted Identity
          Provider. The request should be sent to the Service Provider
          consumer url specified in the SAML2 assertion.
          Providing the authentication was successful and both Service Provider
          and Identity Providers are trusted to each other, the Service
          Provider will issue an unscoped token with a list of groups the
          federated user is a member of.
          This step is handed by a method
          ``Saml2UnscopedToken_send_service_provider_saml2_authn_response()``

          Unscoped token example::

            {
                "token": {
                    "methods": [
                        "saml2"
                    ],
                    "user": {
                        "id": "username%40example.com",
                        "name": "username@example.com",
                        "OS-FEDERATION": {
                            "identity_provider": "ACME",
                            "protocol": "saml2",
                            "groups": [
                                {"id": "abc123"},
                                {"id": "bcd234"}
                            ]
                        }
                    }
                }
            }


        :param session : a session object to send out HTTP requests.
        :type session: keystoneclient.session.Session

        :returns: (token, token_json)

        """
        saml_authenticated = self._send_service_provider_request(session)
        if not saml_authenticated:
            self._send_idp_saml2_authn_request(session)
            self._send_service_provider_saml2_authn_response(session)
        return (self.authenticated_response.headers['X-Subject-Token'],
                self.authenticated_response.json()['token'])

    def get_auth_ref(self, session, **kwargs):
        """Authenticate via SAML2 protocol and retrieve unscoped token.

        This is a multi-step process where a client does federated authn
        receives an unscoped token.

        Federated authentication utilizing SAML2 Enhanced Client or Proxy
        extension. See ``Saml2UnscopedToken_get_unscoped_token()``
        for more information on that step.
        Upon successful authentication and assertion mapping an
        unscoped token is returned and stored within the plugin object for
        further use.

        :param session : a session object to send out HTTP requests.
        :type session: keystoneclient.session.Session

        :return access.AccessInfoV3: an object with scoped token's id and
                                     unscoped token json included.

        """
        token, token_json = self._get_unscoped_token(session, **kwargs)
        return access.AccessInfoV3(token,
                                   **token_json)
