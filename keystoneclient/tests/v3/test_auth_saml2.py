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

import uuid

import httpretty
from lxml import etree
import requests

from keystoneclient.auth import conf
from keystoneclient.contrib.auth.v3 import saml2
from keystoneclient import exceptions
from keystoneclient.openstack.common.fixture import config
from keystoneclient.openstack.common import jsonutils
from keystoneclient import session
from keystoneclient.tests.auth import utils as auth_utils
from keystoneclient.tests.v3 import client_fixtures
from keystoneclient.tests.v3 import saml2_fixtures
from keystoneclient.tests.v3 import utils


class AuthenticateviaSAML2Tests(auth_utils.TestCase, utils.TestCase):

    class _AuthenticatedResponse(object):
        headers = {
            'X-Subject-Token': saml2_fixtures.UNSCOPED_TOKEN_HEADER
        }

        def json(self):
            return saml2_fixtures.UNSCOPED_TOKEN

    class _AuthenticatedResponseInvalidJson(_AuthenticatedResponse):

        def json(self):
            raise ValueError()

    class _AuthentiatedResponseMissingTokenID(_AuthenticatedResponse):
        headers = {}

    def setUp(self):
        utils.TestCase.setUp(self)
        auth_utils.TestCase.setUp(self)

        self.conf_fixture = auth_utils.TestCase.useFixture(self,
                                                           config.Config())
        conf.register_conf_options(self.conf_fixture.conf, group=self.GROUP)

        self.session = session.Session(auth=None, verify=False,
                                       session=requests.Session())
        self.ECP_SP_EMPTY_REQUEST_HEADERS = {
            'Accept': 'text/html; application/vnd.paos+xml',
            'PAOS': ('ver="urn:liberty:paos:2003-08";'
                     '"urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"')
        }

        self.ECP_SP_SAML2_REQUEST_HEADERS = {
            'Content-Type': 'application/vnd.paos+xml'
        }

        self.ECP_SAML2_NAMESPACES = {
            'ecp': 'urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp',
            'S': 'http://schemas.xmlsoap.org/soap/envelope/',
            'paos': 'urn:liberty:paos:2003-08'
        }
        self.ECP_RELAY_STATE = '//ecp:RelayState'
        self.ECP_SERVICE_PROVIDER_CONSUMER_URL = ('/S:Envelope/S:Header/paos:'
                                                  'Request/'
                                                  '@responseConsumerURL')
        self.ECP_IDP_CONSUMER_URL = ('/S:Envelope/S:Header/ecp:Response/'
                                     '@AssertionConsumerServiceURL')
        self.IDENTITY_PROVIDER = 'testidp'
        self.IDENTITY_PROVIDER_URL = 'http://local.url'
        self.PROTOCOL = 'saml2'
        self.FEDERATION_AUTH_URL = '%s/%s' % (
            self.TEST_URL,
            'OS-FEDERATION/identity_providers/testidp/protocols/saml2/auth')
        self.SHIB_CONSUMER_URL = ('https://openstack4.local/'
                                  'Shibboleth.sso/SAML2/ECP')

        self.saml2plugin = saml2.Saml2UnscopedToken(
            self.TEST_URL,
            self.IDENTITY_PROVIDER, self.IDENTITY_PROVIDER_URL,
            self.TEST_USER, self.TEST_TOKEN)

    def simple_http(self, method, url, body=b'', content_type=None,
                    headers=None, status=200, **kwargs):
        self.stub_url(method, base_url=url, body=body, adding_headers=headers,
                      content_type=content_type, status=status, **kwargs)

    def make_oneline(self, s):
        return etree.tostring(etree.XML(s)).replace(b'\n', b'')

    def test_conf_params(self):
        section = uuid.uuid4().hex
        identity_provider = uuid.uuid4().hex
        identity_provider_url = uuid.uuid4().hex
        username = uuid.uuid4().hex
        password = uuid.uuid4().hex
        self.conf_fixture.config(auth_section=section, group=self.GROUP)
        conf.register_conf_options(self.conf_fixture.conf, group=self.GROUP)

        self.conf_fixture.register_opts(saml2.Saml2UnscopedToken.get_options(),
                                        group=section)
        self.conf_fixture.config(auth_plugin='v3unscopedsaml',
                                 identity_provider=identity_provider,
                                 identity_provider_url=identity_provider_url,
                                 username=username,
                                 password=password,
                                 group=section)

        a = conf.load_from_conf_options(self.conf_fixture.conf, self.GROUP)
        self.assertEqual(identity_provider, a.identity_provider)
        self.assertEqual(identity_provider_url, a.identity_provider_url)
        self.assertEqual(username, a.username)
        self.assertEqual(password, a.password)

    @httpretty.activate
    def test_initial_sp_call(self):
        """Test initial call, expect SOAP message."""
        self.simple_http('GET', self.FEDERATION_AUTH_URL,
                         body=self.make_oneline(
                         saml2_fixtures.SP_SOAP_RESPONSE))
        a = self.saml2plugin._send_service_provider_request(self.session)

        self.assertFalse(a)

        fixture_soap_response = self.make_oneline(
            saml2_fixtures.SP_SOAP_RESPONSE)

        sp_soap_response = self.make_oneline(
            etree.tostring(self.saml2plugin.saml2_authn_request))

        error_msg = "Expected %s instead of %s" % (fixture_soap_response,
                                                   sp_soap_response)

        self.assertEqual(fixture_soap_response, sp_soap_response, error_msg)

        self.assertEqual(
            self.saml2plugin.sp_response_consumer_url, self.SHIB_CONSUMER_URL,
            "Expected consumer_url set to %s instead of %s" % (
                self.SHIB_CONSUMER_URL,
                str(self.saml2plugin.sp_response_consumer_url)))

    @httpretty.activate
    def test_initial_sp_call_when_saml_authenticated(self):

        headers = {'X-Subject-Token': saml2_fixtures.UNSCOPED_TOKEN_HEADER}
        self.simple_http('GET', self.FEDERATION_AUTH_URL,
                         body=jsonutils.dumps(saml2_fixtures.UNSCOPED_TOKEN),
                         headers=headers)
        a = self.saml2plugin._send_service_provider_request(self.session)
        self.assertTrue(a)
        self.assertEqual(
            saml2_fixtures.UNSCOPED_TOKEN['token'],
            self.saml2plugin.authenticated_response.json()['token'])
        self.assertEqual(
            saml2_fixtures.UNSCOPED_TOKEN_HEADER,
            self.saml2plugin.authenticated_response.headers['X-Subject-Token'])

    @httpretty.activate
    def test_get_unscoped_token_when_authenticated(self):
        headers = {'X-Subject-Token': saml2_fixtures.UNSCOPED_TOKEN_HEADER}
        self.simple_http('GET', self.FEDERATION_AUTH_URL,
                         body=jsonutils.dumps(saml2_fixtures.UNSCOPED_TOKEN),
                         headers=headers)
        token, token_body = self.saml2plugin._get_unscoped_token(self.session)
        self.assertEqual(saml2_fixtures.UNSCOPED_TOKEN['token'], token_body)

        self.assertEqual(saml2_fixtures.UNSCOPED_TOKEN_HEADER, token)

    @httpretty.activate
    def test_initial_sp_call_invalid_response(self):
        """Send initial SP HTTP request and receive wrong server response."""
        self.simple_http('GET', self.FEDERATION_AUTH_URL,
                         body="NON XML RESPONSE")

        self.assertRaises(
            exceptions.AuthorizationFailure,
            self.saml2plugin._send_service_provider_request,
            self.session)

    @httpretty.activate
    def test_send_authn_req_to_idp(self):
        self.simple_http('POST', self.IDENTITY_PROVIDER_URL,
                         body=saml2_fixtures.SAML2_ASSERTION)

        self.saml2plugin.sp_response_consumer_url = self.SHIB_CONSUMER_URL
        self.saml2plugin.saml2_authn_request = etree.XML(
            saml2_fixtures.SP_SOAP_RESPONSE)
        self.saml2plugin._send_idp_saml2_authn_request(self.session)

        idp_response = self.make_oneline(etree.tostring(
            self.saml2plugin.saml2_idp_authn_response))

        saml2_assertion_oneline = self.make_oneline(
            saml2_fixtures.SAML2_ASSERTION)
        error = "Expected %s instead of %s" % (saml2_fixtures.SAML2_ASSERTION,
                                               idp_response)
        self.assertEqual(idp_response, saml2_assertion_oneline, error)

    @httpretty.activate
    def test_fail_basicauth_idp_authentication(self):
        self.simple_http('POST', self.IDENTITY_PROVIDER_URL,
                         status=401)

        self.saml2plugin.sp_response_consumer_url = self.SHIB_CONSUMER_URL
        self.saml2plugin.saml2_authn_request = etree.XML(
            saml2_fixtures.SP_SOAP_RESPONSE)
        self.assertRaises(
            exceptions.Unauthorized,
            self.saml2plugin._send_idp_saml2_authn_request,
            self.session)

    def test_mising_username_password_in_plugin(self):
        self.assertRaises(TypeError,
                          saml2.Saml2UnscopedToken,
                          self.TEST_URL, self.IDENTITY_PROVIDER,
                          self.IDENTITY_PROVIDER_URL)

    @httpretty.activate
    def test_send_authn_response_to_sp(self):
        self.simple_http(
            'POST', self.SHIB_CONSUMER_URL,
            body=jsonutils.dumps(saml2_fixtures.UNSCOPED_TOKEN),
            content_type='application/json',
            status=200,
            headers={'X-Subject-Token': saml2_fixtures.UNSCOPED_TOKEN_HEADER})

        self.saml2plugin.relay_state = etree.XML(
            saml2_fixtures.SP_SOAP_RESPONSE).xpath(
                self.ECP_RELAY_STATE, namespaces=self.ECP_SAML2_NAMESPACES)[0]

        self.saml2plugin.saml2_idp_authn_response = etree.XML(
            saml2_fixtures.SAML2_ASSERTION)

        self.saml2plugin.idp_response_consumer_url = self.SHIB_CONSUMER_URL
        self.saml2plugin._send_service_provider_saml2_authn_response(
            self.session)
        token_json = self.saml2plugin.authenticated_response.json()['token']
        token = self.saml2plugin.authenticated_response.headers[
            'X-Subject-Token']
        self.assertEqual(saml2_fixtures.UNSCOPED_TOKEN['token'],
                         token_json)

        self.assertEqual(saml2_fixtures.UNSCOPED_TOKEN_HEADER,
                         token)

    def test_consumer_url_mismatch_success(self):
        self.saml2plugin._check_consumer_urls(
            self.session, self.SHIB_CONSUMER_URL,
            self.SHIB_CONSUMER_URL)

    @httpretty.activate
    def test_consumer_url_mismatch(self):
        self.simple_http('POST', self.SHIB_CONSUMER_URL)
        invalid_consumer_url = uuid.uuid4().hex
        self.assertRaises(
            exceptions.ValidationError,
            self.saml2plugin._check_consumer_urls,
            self.session, self.SHIB_CONSUMER_URL,
            invalid_consumer_url)

    @httpretty.activate
    def test_custom_302_redirection(self):
        self.simple_http('POST', self.SHIB_CONSUMER_URL,
                         body='BODY',
                         headers={'location': self.FEDERATION_AUTH_URL},
                         status=302)
        self.simple_http(
            'GET', self.FEDERATION_AUTH_URL,
            body=jsonutils.dumps(saml2_fixtures.UNSCOPED_TOKEN),
            headers={'X-Subject-Token': saml2_fixtures.UNSCOPED_TOKEN_HEADER})
        self.session.redirect = False
        response = self.session.post(
            self.SHIB_CONSUMER_URL, data='CLIENT BODY')
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.FEDERATION_AUTH_URL,
                         response.headers['location'])

        response = self.saml2plugin._handle_http_302_ecp_redirect(
            self.session, response, 'GET')

        self.assertEqual(self.FEDERATION_AUTH_URL, response.request.url)
        self.assertEqual('GET', response.request.method)

    @httpretty.activate
    def test_end_to_end_workflow(self):
        self.simple_http('GET', self.FEDERATION_AUTH_URL,
                         body=self.make_oneline(
                         saml2_fixtures.SP_SOAP_RESPONSE))
        self.simple_http('POST', self.IDENTITY_PROVIDER_URL,
                         body=saml2_fixtures.SAML2_ASSERTION)
        self.simple_http(
            'POST', self.SHIB_CONSUMER_URL,
            body=jsonutils.dumps(saml2_fixtures.UNSCOPED_TOKEN),
            content_type='application/json',
            status=200,
            headers={'X-Subject-Token': saml2_fixtures.UNSCOPED_TOKEN_HEADER})

        self.session.redirect = False
        response = self.saml2plugin.get_auth_ref(self.session)
        self.assertEqual(saml2_fixtures.UNSCOPED_TOKEN_HEADER,
                         response.auth_token)


class ScopeFederationTokenTests(AuthenticateviaSAML2Tests):
    def setUp(self):
        super(ScopeFederationTokenTests, self).setUp()

        self.PROJECT_SCOPED_TOKEN_JSON = client_fixtures.project_scoped_token()
        self.PROJECT_SCOPED_TOKEN_JSON['methods'] = ['saml2']

        # for better readibility
        self.TEST_TENANT_ID = self.PROJECT_SCOPED_TOKEN_JSON.project_id
        self.TEST_TENANT_NAME = self.PROJECT_SCOPED_TOKEN_JSON.project_name

        self.DOMAIN_SCOPED_TOKEN_JSON = client_fixtures.domain_scoped_token()
        self.DOMAIN_SCOPED_TOKEN_JSON['methods'] = ['saml2']

        # for better readibility
        self.TEST_DOMAIN_ID = self.DOMAIN_SCOPED_TOKEN_JSON.domain_id
        self.TEST_DOMAIN_NAME = self.DOMAIN_SCOPED_TOKEN_JSON.domain_name

        self.saml2_scope_plugin = saml2.Saml2ScopedToken(
            self.TEST_URL, saml2_fixtures.UNSCOPED_TOKEN_HEADER,
            project_id=self.TEST_TENANT_ID)

    @httpretty.activate
    def test_scope_saml2_token_to_project(self):
        self.simple_http('POST', self.TEST_URL + '/auth/tokens',
                         body=jsonutils.dumps(self.PROJECT_SCOPED_TOKEN_JSON),
                         content_type='application/json',
                         headers=client_fixtures.AUTH_RESPONSE_HEADERS)

        token = self.saml2_scope_plugin.get_auth_ref(self.session)
        self.assertTrue(token.project_scoped, "Received token is not scoped")
        self.assertEqual(client_fixtures.AUTH_SUBJECT_TOKEN, token.auth_token)
        self.assertEqual(self.TEST_TENANT_ID, token.project_id)
        self.assertEqual(self.TEST_TENANT_NAME, token.project_name)

    @httpretty.activate
    def test_scope_saml2_token_to_invalid_project(self):
        self.simple_http('POST', self.TEST_URL + '/auth/tokens', status=401)
        self.saml2_scope_plugin.project_id = uuid.uuid4().hex
        self.saml2_scope_plugin.project_name = None
        self.assertRaises(exceptions.Unauthorized,
                          self.saml2_scope_plugin.get_auth_ref,
                          self.session)

    @httpretty.activate
    def test_scope_saml2_token_to_invalid_domain(self):
        self.simple_http('POST', self.TEST_URL + '/auth/tokens', status=401)
        self.saml2_scope_plugin.project_id = None
        self.saml2_scope_plugin.project_name = None
        self.saml2_scope_plugin.domain_id = uuid.uuid4().hex
        self.saml2_scope_plugin.domain_name = None
        self.assertRaises(exceptions.Unauthorized,
                          self.saml2_scope_plugin.get_auth_ref,
                          self.session)

    @httpretty.activate
    def test_scope_saml2_token_to_domain(self):
        self.simple_http('POST', self.TEST_URL + '/auth/tokens',
                         body=jsonutils.dumps(self.DOMAIN_SCOPED_TOKEN_JSON),
                         content_type='application/json',
                         headers=client_fixtures.AUTH_RESPONSE_HEADERS)

        token = self.saml2_scope_plugin.get_auth_ref(self.session)
        self.assertTrue(token.domain_scoped, "Received token is not scoped")
        self.assertEqual(client_fixtures.AUTH_SUBJECT_TOKEN, token.auth_token)
        self.assertEqual(self.TEST_DOMAIN_ID, token.domain_id)
        self.assertEqual(self.TEST_DOMAIN_NAME, token.domain_name)

    def test_dont_set_project_nor_domain(self):
        self.saml2_scope_plugin.project_id = None
        self.saml2_scope_plugin.domain_id = None
        self.assertRaises(exceptions.ValidationError,
                          saml2.Saml2ScopedToken,
                          self.TEST_URL, client_fixtures.AUTH_SUBJECT_TOKEN)
