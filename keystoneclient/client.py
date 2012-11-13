# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
# Copyright 2011 Nebula, Inc.

# All Rights Reserved.
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import copy
import logging
import urlparse

import httplib2

try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from keystoneclient import access
from keystoneclient import exceptions


_logger = logging.getLogger(__name__)


class HTTPClient(httplib2.Http):

    USER_AGENT = 'python-keystoneclient'

    def __init__(self, username=None, tenant_id=None, tenant_name=None,
                 password=None, auth_url=None, region_name=None, timeout=None,
                 endpoint=None, token=None, cacert=None, key=None,
                 cert=None, insecure=False, original_ip=None, debug=False,
                 auth_ref=None):
        super(HTTPClient, self).__init__(timeout=timeout, ca_certs=cacert)
        if cert:
            if key:
                self.add_certificate(key=key, cert=cert, domain='')
            else:
                self.add_certificate(key=cert, cert=cert, domain='')
        self.version = 'v2.0'
        self.auth_ref = access.AccessInfo(**auth_ref) if auth_ref else None
        if self.auth_ref:
            self.username = self.auth_ref.username
            self.tenant_id = self.auth_ref.tenant_id
            self.tenant_name = self.auth_ref.tenant_name
            self.auth_url = self.auth_ref.auth_url
            self.management_url = self.auth_ref.management_url
            self.auth_token = self.auth_ref.auth_token
        #NOTE(heckj): allow override of the auth_ref defaults from explicit
        # values provided to the client
        self.username = username
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.password = password
        self.auth_url = auth_url.rstrip('/') if auth_url else None
        self.auth_token = token
        self.original_ip = original_ip

        self.management_url = endpoint.rstrip('/') if endpoint else None
        self.region_name = region_name

        # httplib2 overrides
        self.force_exception_to_status_code = True
        self.disable_ssl_certificate_validation = insecure

        # logging setup
        self.debug_log = debug
        if self.debug_log:
            ch = logging.StreamHandler()
            _logger.setLevel(logging.DEBUG)
            _logger.addHandler(ch)
	else:
	    logging.raiseExceptions = 0
	    

    def authenticate(self):
        """ Authenticate against the Identity API.

        Not implemented here because auth protocols should be API
        version-specific.

        Expected to authenticate or validate an existing authentication
        reference already associated with the client. Invoking this call
        *always* makes a call to the Keystone.
        """
        raise NotImplementedError

    def _extract_service_catalog(self, url, body):
        """ Set the client's service catalog from the response data.

        Not implemented here because data returned may be API
        version-specific.
        """
        raise NotImplementedError

    def http_log_req(self, args, kwargs):
        if not self.debug_log:
            return

        string_parts = ['curl -i']
        for element in args:
            if element in ('GET', 'POST'):
                string_parts.append(' -X %s' % element)
            else:
                string_parts.append(' %s' % element)

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        _logger.debug("REQ: %s\n" % "".join(string_parts))
        if 'body' in kwargs:
            _logger.debug("REQ BODY: %s\n" % (kwargs['body']))

    def http_log_resp(self, resp, body):
        if self.debug_log:
            _logger.debug("RESP: %s\nRESP BODY: %s\n", resp, body)

    def serialize(self, entity):
        return json.dumps(entity)

    def request(self, url, method, **kwargs):
        """ Send an http request with the specified characteristics.

        Wrapper around httplib2.Http.request to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.
        """
        # Copy the kwargs so we can reuse the original in case of redirects
        request_kwargs = copy.copy(kwargs)
        request_kwargs.setdefault('headers', kwargs.get('headers', {}))
        request_kwargs['headers']['User-Agent'] = self.USER_AGENT
        if self.original_ip:
            request_kwargs['headers']['Forwarded'] = "for=%s;by=%s" % (
                self.original_ip, self.USER_AGENT)
        if 'body' in kwargs:
            request_kwargs['headers']['Content-Type'] = 'application/json'
            request_kwargs['body'] = self.serialize(kwargs['body'])

        self.http_log_req((url, method,), request_kwargs)
        resp, body = super(HTTPClient, self).request(url,
                                                     method,
                                                     **request_kwargs)
        self.http_log_resp(resp, body)

        if resp.status in (400, 401, 403, 404, 408, 409, 413, 500, 501):
            _logger.debug("Request returned failure status: %s", resp.status)
            raise exceptions.from_response(resp, body)
        elif resp.status in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self.request(resp['location'], method, **kwargs)

        if body:
            try:
                body = json.loads(body)
            except ValueError:
                _logger.debug("Could not decode JSON from body: %s" % body)
        else:
            _logger.debug("No body was returned.")
            body = None

        return resp, body

    def _cs_request(self, url, method, **kwargs):
        """ Makes an authenticated request to keystone endpoint by
        concatenating self.management_url and url and passing in method and
        any associated kwargs. """

        if self.management_url is None:
            raise exceptions.AuthorizationFailure(
                'Current authorization does not have a known management url')
        kwargs.setdefault('headers', {})
        if self.auth_token:
            kwargs['headers']['X-Auth-Token'] = self.auth_token

        resp, body = self.request(self.management_url + url, method,
                                  **kwargs)
        return resp, body

    def get(self, url, **kwargs):
        return self._cs_request(url, 'GET', **kwargs)

    def head(self, url, **kwargs):
        return self._cs_request(url, 'HEAD', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def patch(self, url, **kwargs):
        return self._cs_request(url, 'PATCH', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)
