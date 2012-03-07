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
import os
import time
import urllib
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


from keystoneclient import exceptions


_logger = logging.getLogger(__name__)


class HTTPClient(httplib2.Http):

    USER_AGENT = 'python-keystoneclient'

    def __init__(self, username=None, tenant_id=None, tenant_name=None,
                 password=None, auth_url=None, region_name=None, timeout=None,
                 endpoint=None, token=None):
        super(HTTPClient, self).__init__(timeout=timeout)
        self.username = username
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.password = password
        self.auth_url = auth_url.rstrip('/') if auth_url else None
        self.version = 'v2.0'
        self.region_name = region_name
        self.auth_token = token

        self.management_url = endpoint

        # httplib2 overrides
        self.force_exception_to_status_code = True

    def authenticate(self):
        """ Authenticate against the keystone API.

        Not implemented here because auth protocols should be API
        version-specific.
        """
        raise NotImplementedError

    def _extract_service_catalog(self, url, body):
        """ Set the client's service catalog from the response data.

        Not implemented here because data returned may be API
        version-specific.
        """
        raise NotImplementedError

    def http_log(self, args, kwargs, resp, body):
        if os.environ.get('KEYSTONECLIENT_DEBUG', False):
            ch = logging.StreamHandler()
            _logger.setLevel(logging.DEBUG)
            _logger.addHandler(ch)
        elif not _logger.isEnabledFor(logging.DEBUG):
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
        _logger.debug("RESP: %s\nRESP BODY: %s\n", resp, body)

    def request(self, url, method, **kwargs):
        """ Send an http request with the specified characteristics.

        Wrapper around httplib2.Http.request to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.
        """
        # Copy the kwargs so we can reuse the original in case of redirects
        request_kwargs = copy.copy(kwargs)
        request_kwargs.setdefault('headers', kwargs.get('headers', {}))
        request_kwargs['headers']['User-Agent'] = self.USER_AGENT
        if 'body' in kwargs:
            request_kwargs['headers']['Content-Type'] = 'application/json'
            request_kwargs['body'] = json.dumps(kwargs['body'])

        resp, body = super(HTTPClient, self).request(url,
                                                     method,
                                                     **request_kwargs)

        self.http_log((url, method,), request_kwargs, resp, body)

        if body:
            try:
                body = json.loads(body)
            except ValueError, e:
                _logger.debug("Could not decode JSON from body: %s" % body)
        else:
            _logger.debug("No body was returned.")
            body = None

        if resp.status in (400, 401, 403, 404, 408, 409, 413, 500, 501):
            _logger.exception("Request returned failure status.")
            raise exceptions.from_response(resp, body)
        elif resp.status in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self.request(resp['location'], method, **kwargs)

        return resp, body

    def _cs_request(self, url, method, **kwargs):
        if not self.management_url:
            self.authenticate()

        kwargs.setdefault('headers', {})
        if self.auth_token:
            kwargs['headers']['X-Auth-Token'] = self.auth_token

        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            resp, body = self.request(self.management_url + url, method,
                                      **kwargs)
            return resp, body
        except exceptions.Unauthorized:
            try:
                if getattr(self, '_failures', 0) < 1:
                    self._failures = getattr(self, '_failures', 0) + 1
                    self.authenticate()
                    resp, body = self.request(self.management_url + url,
                                              method, **kwargs)
                    return resp, body
                else:
                    raise
            except exceptions.Unauthorized:
                raise

    def get(self, url, **kwargs):
        return self._cs_request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self._cs_request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._cs_request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._cs_request(url, 'DELETE', **kwargs)
