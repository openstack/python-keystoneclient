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

SP_SOAP_RESPONSE = b"""<S:Envelope
xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
<S:Header>
<paos:Request xmlns:paos="urn:liberty:paos:2003-08"
S:actor="http://schemas.xmlsoap.org/soap/actor/next"
S:mustUnderstand="1"
responseConsumerURL="https://openstack4.local/Shibboleth.sso/SAML2/ECP"
service="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"/>
<ecp:Request xmlns:ecp="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"
IsPassive="0" S:actor="http://schemas.xmlsoap.org/soap/actor/next"
S:mustUnderstand="1">
<saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
https://openstack4.local/shibboleth
</saml:Issuer>
<samlp:IDPList xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol">
<samlp:IDPEntry ProviderID="https://idp.testshib.org/idp/shibboleth"/>
</samlp:IDPList></ecp:Request>
<ecp:RelayState xmlns:ecp="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"
S:actor="http://schemas.xmlsoap.org/soap/actor/next" S:mustUnderstand="1">
ss:mem:6f1f20fafbb38433467e9d477df67615</ecp:RelayState>
</S:Header><S:Body><samlp:AuthnRequest
xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
AssertionConsumerServiceURL="https://openstack4.local/Shibboleth.sso/SAML2/ECP"
 ID="_a07186e3992e70e92c17b9d249495643" IssueInstant="2014-06-09T09:48:57Z"
 ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:PAOS" Version="2.0">
 <saml:Issuer
 xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
 https://openstack4.local/shibboleth
 </saml:Issuer><samlp:NameIDPolicy AllowCreate="1"/><samlp:Scoping>
 <samlp:IDPList>
 <samlp:IDPEntry ProviderID="https://idp.testshib.org/idp/shibboleth"/>
 </samlp:IDPList></samlp:Scoping></samlp:AuthnRequest></S:Body></S:Envelope>
"""


SAML2_ASSERTION = b"""<?xml version="1.0" encoding="UTF-8"?>
<soap11:Envelope xmlns:soap11="http://schemas.xmlsoap.org/soap/envelope/">
<soap11:Header>
<ecp:Response xmlns:ecp="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"
AssertionConsumerServiceURL="https://openstack4.local/Shibboleth.sso/SAML2/ECP"
 soap11:actor="http://schemas.xmlsoap.org/soap/actor/next"
 soap11:mustUnderstand="1"/>
 <samlec:GeneratedKey xmlns:samlec="urn:ietf:params:xml:ns:samlec"
 soap11:actor="http://schemas.xmlsoap.org/soap/actor/next">
 x=
 </samlec:GeneratedKey>
 </soap11:Header>
 <soap11:Body>
 <saml2p:Response xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol"
Destination="https://openstack4.local/Shibboleth.sso/SAML2/ECP"
ID="_bbbe6298d7ee586c915d952013875440"
InResponseTo="_a07186e3992e70e92c17b9d249495643"
IssueInstant="2014-06-09T09:48:58.945Z" Version="2.0">
<saml2:Issuer xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"
Format="urn:oasis:names:tc:SAML:2.0:nameid-format:entity">
https://idp.testshib.org/idp/shibboleth
</saml2:Issuer><saml2p:Status>
<saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
</saml2p:Status>
<saml2:EncryptedAssertion xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion">
<xenc:EncryptedData xmlns:xenc="http://www.w3.org/2001/04/xmlenc#"
Id="_e5215ac77a6028a8da8caa8be89bad44"
Type="http://www.w3.org/2001/04/xmlenc#Element">
<xenc:EncryptionMethod Algorithm="http://www.w3.org/2001/04/xmlenc#aes128-cbc"
xmlns:xenc="http://www.w3.org/2001/04/xmlenc#"/>
<ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
<xenc:EncryptedKey Id="_204349856f6e73c9480afc949d1b4643"
xmlns:xenc="http://www.w3.org/2001/04/xmlenc#">
<xenc:EncryptionMethod
Algorithm="http://www.w3.org/2001/04/xmlenc#rsa-oaep-mgf1p"
xmlns:xenc="http://www.w3.org/2001/04/xmlenc#">
<ds:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"
xmlns:ds="http://www.w3.org/2000/09/xmldsig#"/>
</xenc:EncryptionMethod><ds:KeyInfo><ds:X509Data><ds:X509Certificate>
</ds:X509Certificate>
</ds:X509Data></ds:KeyInfo>
<xenc:CipherData xmlns:xenc="http://www.w3.org/2001/04/xmlenc#">
<xenc:CipherValue>VALUE==</xenc:CipherValue></xenc:CipherData>
</xenc:EncryptedKey></ds:KeyInfo>
<xenc:CipherData xmlns:xenc="http://www.w3.org/2001/04/xmlenc#">
<xenc:CipherValue>VALUE=</xenc:CipherValue></xenc:CipherData>
</xenc:EncryptedData></saml2:EncryptedAssertion></saml2p:Response>
</soap11:Body></soap11:Envelope>
"""

UNSCOPED_TOKEN_HEADER = 'UNSCOPED_TOKEN'

UNSCOPED_TOKEN = {
    "token": {
        "issued_at": "2014-06-09T09:48:59.643406Z",
        "extras": {},
        "methods": ["saml2"],
        "expires_at": "2014-06-09T10:48:59.643375Z",
        "user": {
            "OS-FEDERATION": {
                "identity_provider": {
                    "id": "testshib"
                },
                "protocol": {
                    "id": "saml2"
                },
                "groups": [
                    {"id": "1764fa5cf69a49a4918131de5ce4af9a"}
                ]
            },
            "id": "testhib%20user",
            "name": "testhib user"
        }
    }
}

PROJECTS = {
    "projects": [
        {
            "domain_id": "37ef61",
            "enabled": 'true',
            "id": "12d706",
            "links": {
                "self": "http://identity:35357/v3/projects/12d706"
            },
            "name": "a project name"
        },
        {
            "domain_id": "37ef61",
            "enabled": 'true',
            "id": "9ca0eb",
            "links": {
                "self": "http://identity:35357/v3/projects/9ca0eb"
            },
            "name": "another project"
        }
    ],
    "links": {
        "self": "http://identity:35357/v3/auth/projects",
        "previous": 'null',
        "next": 'null'
    }
}

DOMAINS = {
    "domains": [
        {
            "description": "desc of domain",
            "enabled": 'true',
            "id": "37ef61",
            "links": {
                "self": "http://identity:35357/v3/domains/37ef61"
            },
            "name": "my domain"
        }
    ],
    "links": {
        "self": "http://identity:35357/v3/auth/domains",
        "previous": 'null',
        "next": 'null'
    }
}

SAML_ENCODING = "<?xml version='1.0' encoding='UTF-8'?>"

TOKEN_SAML_RESPONSE = """
<ns2:Response Destination="http://beta.example.com/Shibboleth.sso/POST/ECP"
  ID="8c21de08d2f2435c9acf13e72c982846"
  IssueInstant="2015-03-25T14:43:21Z"
  Version="2.0">
  <saml:Issuer Format="urn:oasis:names:tc:SAML:2.0:nameid-format:entity">
    http://keystone.idp/v3/OS-FEDERATION/saml2/idp
  </saml:Issuer>
  <ns2:Status>
    <ns2:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
  </ns2:Status>
  <saml:Assertion ID="a5f02efb0bff4044b294b4583c7dfc5d"
    IssueInstant="2015-03-25T14:43:21Z" Version="2.0">
  <saml:Issuer Format="urn:oasis:names:tc:SAML:2.0:nameid-format:entity">
    http://keystone.idp/v3/OS-FEDERATION/saml2/idp</saml:Issuer>
  <xmldsig:Signature>
    <xmldsig:SignedInfo>
      <xmldsig:CanonicalizationMethod
        Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
      <xmldsig:SignatureMethod
        Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
      <xmldsig:Reference URI="#a5f02efb0bff4044b294b4583c7dfc5d">
        <xmldsig:Transforms>
          <xmldsig:Transform
             Algorithm="http://www.w3.org/2000/09/xmldsig#
             enveloped-signature"/>
          <xmldsig:Transform
             Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
        </xmldsig:Transforms>
        <xmldsig:DigestMethod
          Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
        <xmldsig:DigestValue>
          0KH2CxdkfzU+6eiRhTC+mbObUKI=
        </xmldsig:DigestValue>
      </xmldsig:Reference>
    </xmldsig:SignedInfo>
    <xmldsig:SignatureValue>
      m2jh5gDvX/1k+4uKtbb08CHp2b9UWsLw
    </xmldsig:SignatureValue>
    <xmldsig:KeyInfo>
      <xmldsig:X509Data>
        <xmldsig:X509Certificate>...</xmldsig:X509Certificate>
      </xmldsig:X509Data>
    </xmldsig:KeyInfo>
  </xmldsig:Signature>
  <saml:Subject>
    <saml:NameID>admin</saml:NameID>
    <saml:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
      <saml:SubjectConfirmationData
        NotOnOrAfter="2015-03-25T15:43:21.172385Z"
        Recipient="http://beta.example.com/Shibboleth.sso/POST/ECP"/>
    </saml:SubjectConfirmation>
  </saml:Subject>
  <saml:AuthnStatement AuthnInstant="2015-03-25T14:43:21Z"
    SessionIndex="9790eb729858456f8a33b7a11f0a637e"
    SessionNotOnOrAfter="2015-03-25T15:43:21.172385Z">
    <saml:AuthnContext>
      <saml:AuthnContextClassRef>
        urn:oasis:names:tc:SAML:2.0:ac:classes:Password
      </saml:AuthnContextClassRef>
      <saml:AuthenticatingAuthority>
        http://keystone.idp/v3/OS-FEDERATION/saml2/idp
      </saml:AuthenticatingAuthority>
    </saml:AuthnContext>
  </saml:AuthnStatement>
  <saml:AttributeStatement>
    <saml:Attribute Name="openstack_user"
      NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri">
      <saml:AttributeValue xsi:type="xs:string">admin</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="openstack_roles"
      NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri">
      <saml:AttributeValue xsi:type="xs:string">admin</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="openstack_project"
      NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri">
      <saml:AttributeValue xsi:type="xs:string">admin</saml:AttributeValue>
    </saml:Attribute>
  </saml:AttributeStatement>
  </saml:Assertion>
</ns2:Response>
"""

TOKEN_BASED_SAML = ''.join([SAML_ENCODING, TOKEN_SAML_RESPONSE])

ECP_ENVELOPE = """
<ns0:Envelope
  xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:ns1="urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"
  xmlns:ns2="urn:oasis:names:tc:SAML:2.0:protocol"
  xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
  xmlns:xmldsig="http://www.w3.org/2000/09/xmldsig#"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <ns0:Header>
    <ns1:RelayState
      ns0:actor="http://schemas.xmlsoap.org/soap/actor/next"
      ns0:mustUnderstand="1">
        ss:mem:1ddfe8b0f58341a5a840d2e8717b0737
      </ns1:RelayState>
  </ns0:Header>
  <ns0:Body>
  {0}
  </ns0:Body>
</ns0:Envelope>
""".format(TOKEN_SAML_RESPONSE)

TOKEN_BASED_ECP = ''.join([SAML_ENCODING, ECP_ENVELOPE])
