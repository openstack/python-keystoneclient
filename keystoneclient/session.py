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

import argparse
import functools
import hashlib
import logging
import os
import socket
import time
import warnings

from debtcollector import removals
from oslo_config import cfg
from oslo_serialization import jsonutils
from oslo_utils import encodeutils
from oslo_utils import importutils
from oslo_utils import strutils
from positional import positional
import requests
import six
from six.moves import urllib

from keystoneclient import exceptions
from keystoneclient.i18n import _

osprofiler_web = importutils.try_import("osprofiler.web")

USER_AGENT = 'python-keystoneclient'

# NOTE(jamielennox): Clients will likely want to print more than json. Please
# propose a patch if you have a content type you think is reasonable to print
# here and we'll add it to the list as required.
_LOG_CONTENT_TYPES = set(['application/json'])

_logger = logging.getLogger(__name__)


def _positive_non_zero_float(argument_value):
    if argument_value is None:
        return None
    try:
        value = float(argument_value)
    except ValueError:
        msg = _("%s must be a float") % argument_value
        raise argparse.ArgumentTypeError(msg)
    if value <= 0:
        msg = _("%s must be greater than 0") % argument_value
        raise argparse.ArgumentTypeError(msg)
    return value


def request(url, method='GET', **kwargs):
    return Session().request(url, method=method, **kwargs)


def _remove_service_catalog(body):
    try:
        data = jsonutils.loads(body)

        # V3 token
        if 'token' in data and 'catalog' in data['token']:
            data['token']['catalog'] = '<removed>'
            return jsonutils.dumps(data)

        # V2 token
        if 'serviceCatalog' in data['access']:
            data['access']['serviceCatalog'] = '<removed>'
            return jsonutils.dumps(data)

    except Exception:  # nosec(cjschaef): multiple exceptions can be raised
        # Don't fail trying to clean up the request body.
        pass
    return body


class Session(object):
    """Maintains client communication state and common functionality.

    As much as possible the parameters to this class reflect and are passed
    directly to the requests library.

    :param auth: An authentication plugin to authenticate the session with.
                 (optional, defaults to None)
    :type auth: :py:class:`keystoneclient.auth.base.BaseAuthPlugin`
    :param requests.Session session: A requests session object that can be used
                                     for issuing requests. (optional)
    :param string original_ip: The original IP of the requesting user which
                               will be sent to identity service in a
                               'Forwarded' header. (optional)
    :param verify: The verification arguments to pass to requests. These are of
                   the same form as requests expects, so True or False to
                   verify (or not) against system certificates or a path to a
                   bundle or CA certs to check against or None for requests to
                   attempt to locate and use certificates. (optional, defaults
                   to True)
    :param cert: A client certificate to pass to requests. These are of the
                 same form as requests expects. Either a single filename
                 containing both the certificate and key or a tuple containing
                 the path to the certificate then a path to the key. (optional)
    :param float timeout: A timeout to pass to requests. This should be a
                          numerical value indicating some amount (or fraction)
                          of seconds or 0 for no timeout. (optional, defaults
                          to 0)
    :param string user_agent: A User-Agent header string to use for the
                              request. If not provided a default is used.
                              (optional, defaults to 'python-keystoneclient')
    :param int/bool redirect: Controls the maximum number of redirections that
                              can be followed by a request. Either an integer
                              for a specific count or True/False for
                              forever/never. (optional, default to 30)
    """

    user_agent = None

    _REDIRECT_STATUSES = (301, 302, 303, 305, 307)

    REDIRECT_STATUSES = _REDIRECT_STATUSES
    """This property is deprecated as of the 1.7.0 release and may be removed
       in the 2.0.0 release."""

    _DEFAULT_REDIRECT_LIMIT = 30

    DEFAULT_REDIRECT_LIMIT = _DEFAULT_REDIRECT_LIMIT
    """This property is deprecated as of the 1.7.0 release and may be removed
       in the 2.0.0 release."""

    @positional(2, enforcement=positional.WARN)
    def __init__(self, auth=None, session=None, original_ip=None, verify=True,
                 cert=None, timeout=None, user_agent=None,
                 redirect=_DEFAULT_REDIRECT_LIMIT):
        warnings.warn(
            'keystoneclient.session.Session is deprecated as of the 2.1.0 '
            'release in favor of keystoneauth1.session.Session. It will be '
            'removed in future releases.',
            DeprecationWarning)

        if not session:
            session = requests.Session()
            # Use TCPKeepAliveAdapter to fix bug 1323862
            for scheme in list(session.adapters):
                session.mount(scheme, TCPKeepAliveAdapter())

        self.auth = auth
        self.session = session
        self.original_ip = original_ip
        self.verify = verify
        self.cert = cert
        self.timeout = None
        self.redirect = redirect

        if timeout is not None:
            self.timeout = float(timeout)

        # don't override the class variable if none provided
        if user_agent is not None:
            self.user_agent = user_agent

    @staticmethod
    def _process_header(header):
        """Redact the secure headers to be logged."""
        secure_headers = ('authorization', 'x-auth-token',
                          'x-subject-token', 'x-service-token')
        if header[0].lower() in secure_headers:
            # hashlib.sha1() bandit nosec, as it is HMAC-SHA1 in
            # keystone, which is considered secure (unlike just sha1)
            token_hasher = hashlib.sha1()  # nosec(lhinds)
            token_hasher.update(header[1].encode('utf-8'))
            token_hash = token_hasher.hexdigest()
            return (header[0], '{SHA1}%s' % token_hash)
        return header

    @positional()
    def _http_log_request(self, url, method=None, data=None,
                          headers=None, logger=_logger):
        if not logger.isEnabledFor(logging.DEBUG):
            # NOTE(morganfainberg): This whole debug section is expensive,
            # there is no need to do the work if we're not going to emit a
            # debug log.
            return

        string_parts = ['REQ: curl -g -i']

        # NOTE(jamielennox): None means let requests do its default validation
        # so we need to actually check that this is False.
        if self.verify is False:
            string_parts.append('--insecure')
        elif isinstance(self.verify, six.string_types):
            string_parts.append('--cacert "%s"' % self.verify)

        if method:
            string_parts.extend(['-X', method])

        string_parts.append(url)

        if headers:
            for header in headers.items():
                string_parts.append('-H "%s: %s"'
                                    % self._process_header(header))

        if data:
            if isinstance(data, six.binary_type):
                try:
                    data = data.decode("ascii")
                except UnicodeDecodeError:
                    data = "<binary_data>"
            string_parts.append("-d '%s'" % data)
        try:
            logger.debug(' '.join(string_parts))
        except UnicodeDecodeError:
            logger.debug("Replaced characters that could not be decoded"
                         " in log output, original caused UnicodeDecodeError")
            string_parts = [
                encodeutils.safe_decode(
                    part, errors='replace') for part in string_parts]
            logger.debug(' '.join(string_parts))

    def _http_log_response(self, response, logger):
        if not logger.isEnabledFor(logging.DEBUG):
            return

        # NOTE(samueldmq): If the response does not provide enough info about
        # the content type to decide whether it is useful and safe to log it
        # or not, just do not log the body. Trying to# read the response body
        # anyways may result on reading a long stream of bytes and getting an
        # unexpected MemoryError. See bug 1616105 for further details.
        content_type = response.headers.get('content-type', None)

        # NOTE(lamt): Per [1], the Content-Type header can be of the form
        # Content-Type := type "/" subtype *[";" parameter]
        # [1] https://www.w3.org/Protocols/rfc1341/4_Content-Type.html
        for log_type in _LOG_CONTENT_TYPES:
            if content_type is not None and content_type.startswith(log_type):
                text = _remove_service_catalog(response.text)
                break
        else:
            text = ('Omitted, Content-Type is set to %s. Only '
                    '%s responses have their bodies logged.')
            text = text % (content_type, ', '.join(_LOG_CONTENT_TYPES))

        string_parts = [
            'RESP:',
            '[%s]' % response.status_code
        ]
        for header in response.headers.items():
            string_parts.append('%s: %s' % self._process_header(header))
        string_parts.append('\nRESP BODY: %s\n' % strutils.mask_password(text))

        logger.debug(' '.join(string_parts))

    # NOTE(artmr): parameter 'original_ip' value is never used
    @positional(enforcement=positional.WARN)
    def request(self, url, method, json=None, original_ip=None,
                user_agent=None, redirect=None, authenticated=None,
                endpoint_filter=None, auth=None, requests_auth=None,
                raise_exc=True, allow_reauth=True, log=True,
                endpoint_override=None, connect_retries=0, logger=_logger,
                **kwargs):
        """Send an HTTP request with the specified characteristics.

        Wrapper around `requests.Session.request` to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.

        Arguments that are not handled are passed through to the requests
        library.

        :param string url: Path or fully qualified URL of HTTP request. If only
                           a path is provided then endpoint_filter must also be
                           provided such that the base URL can be determined.
                           If a fully qualified URL is provided then
                           endpoint_filter will be ignored.
        :param string method: The http method to use. (e.g. 'GET', 'POST')
        :param string original_ip: Mark this request as forwarded for this ip.
                                   (optional)
        :param dict headers: Headers to be included in the request. (optional)
        :param json: Some data to be represented as JSON. (optional)
        :param string user_agent: A user_agent to use for the request. If
                                  present will override one present in headers.
                                  (optional)
        :param int/bool redirect: the maximum number of redirections that
                                  can be followed by a request. Either an
                                  integer for a specific count or True/False
                                  for forever/never. (optional)
        :param int connect_retries: the maximum number of retries that should
                                    be attempted for connection errors.
                                    (optional, defaults to 0 - never retry).
        :param bool authenticated: True if a token should be attached to this
                                   request, False if not or None for attach if
                                   an auth_plugin is available.
                                   (optional, defaults to None)
        :param dict endpoint_filter: Data to be provided to an auth plugin with
                                     which it should be able to determine an
                                     endpoint to use for this request. If not
                                     provided then URL is expected to be a
                                     fully qualified URL. (optional)
        :param str endpoint_override: The URL to use instead of looking up the
                                      endpoint in the auth plugin. This will be
                                      ignored if a fully qualified URL is
                                      provided but take priority over an
                                      endpoint_filter. (optional)
        :param auth: The auth plugin to use when authenticating this request.
                     This will override the plugin that is attached to the
                     session (if any). (optional)
        :type auth: :py:class:`keystoneclient.auth.base.BaseAuthPlugin`
        :param requests_auth: A requests library auth plugin that cannot be
                              passed via kwarg because the `auth` kwarg
                              collides with our own auth plugins. (optional)
        :type requests_auth: :py:class:`requests.auth.AuthBase`
        :param bool raise_exc: If True then raise an appropriate exception for
                               failed HTTP requests. If False then return the
                               request object. (optional, default True)
        :param bool allow_reauth: Allow fetching a new token and retrying the
                                  request on receiving a 401 Unauthorized
                                  response. (optional, default True)
        :param bool log: If True then log the request and response data to the
                         debug log. (optional, default True)
        :param logger: The logger object to use to log request and responses.
                       If not provided the keystoneclient.session default
                       logger will be used.
        :type logger: logging.Logger
        :param kwargs: any other parameter that can be passed to
                       requests.Session.request (such as `headers`). Except:
                       'data' will be overwritten by the data in 'json' param.
                       'allow_redirects' is ignored as redirects are handled
                       by the session.

        :raises keystoneclient.exceptions.ClientException: For connection
            failure, or to indicate an error response code.

        :returns: The response to the request.
        """
        headers = kwargs.setdefault('headers', dict())

        if authenticated is None:
            authenticated = bool(auth or self.auth)

        if authenticated:
            auth_headers = self.get_auth_headers(auth)

            if auth_headers is None:
                msg = _('No valid authentication is available')
                raise exceptions.AuthorizationFailure(msg)

            headers.update(auth_headers)

        if osprofiler_web:
            headers.update(osprofiler_web.get_trace_id_headers())

        # if we are passed a fully qualified URL and an endpoint_filter we
        # should ignore the filter. This will make it easier for clients who
        # want to overrule the default endpoint_filter data added to all client
        # requests. We check fully qualified here by the presence of a host.
        if not urllib.parse.urlparse(url).netloc:
            base_url = None

            if endpoint_override:
                base_url = endpoint_override
            elif endpoint_filter:
                base_url = self.get_endpoint(auth, **endpoint_filter)

            if not base_url:
                service_type = (endpoint_filter or {}).get('service_type',
                                                           'unknown')
                msg = _('Endpoint for %s service') % service_type
                raise exceptions.EndpointNotFound(msg)

            url = '%s/%s' % (base_url.rstrip('/'), url.lstrip('/'))

        if self.cert:
            kwargs.setdefault('cert', self.cert)

        if self.timeout is not None:
            kwargs.setdefault('timeout', self.timeout)

        if user_agent:
            headers['User-Agent'] = user_agent
        elif self.user_agent:
            user_agent = headers.setdefault('User-Agent', self.user_agent)
        else:
            user_agent = headers.setdefault('User-Agent', USER_AGENT)

        if self.original_ip:
            headers.setdefault('Forwarded',
                               'for=%s;by=%s' % (self.original_ip, user_agent))

        if json is not None:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = jsonutils.dumps(json)

        kwargs.setdefault('verify', self.verify)

        if requests_auth:
            kwargs['auth'] = requests_auth

        if log:
            self._http_log_request(url, method=method,
                                   data=kwargs.get('data'),
                                   headers=headers,
                                   logger=logger)

        # Force disable requests redirect handling. We will manage this below.
        kwargs['allow_redirects'] = False

        if redirect is None:
            redirect = self.redirect

        send = functools.partial(self._send_request,
                                 url, method, redirect, log, logger,
                                 connect_retries)

        try:
            connection_params = self.get_auth_connection_params(auth=auth)
        except exceptions.MissingAuthPlugin:  # nosec(cjschaef)
            # NOTE(jamielennox): If we've gotten this far without an auth
            # plugin then we should be happy with allowing no additional
            # connection params. This will be the typical case for plugins
            # anyway.
            pass
        else:
            if connection_params:
                kwargs.update(connection_params)

        resp = send(**kwargs)

        # handle getting a 401 Unauthorized response by invalidating the plugin
        # and then retrying the request. This is only tried once.
        if resp.status_code == 401 and authenticated and allow_reauth:
            if self.invalidate(auth):
                auth_headers = self.get_auth_headers(auth)

                if auth_headers is not None:
                    headers.update(auth_headers)
                    resp = send(**kwargs)

        if raise_exc and resp.status_code >= 400:
            logger.debug('Request returned failure status: %s',
                         resp.status_code)
            raise exceptions.from_response(resp, method, url)

        return resp

    def _send_request(self, url, method, redirect, log, logger,
                      connect_retries, connect_retry_delay=0.5, **kwargs):
        # NOTE(jamielennox): We handle redirection manually because the
        # requests lib follows some browser patterns where it will redirect
        # POSTs as GETs for certain statuses which is not want we want for an
        # API. See: https://en.wikipedia.org/wiki/Post/Redirect/Get

        # NOTE(jamielennox): The interaction between retries and redirects are
        # handled naively. We will attempt only a maximum number of retries and
        # redirects rather than per request limits. Otherwise the extreme case
        # could be redirects * retries requests. This will be sufficient in
        # most cases and can be fixed properly if there's ever a need.

        try:
            try:
                resp = self.session.request(method, url, **kwargs)
            except requests.exceptions.SSLError as e:
                msg = _('SSL exception connecting to %(url)s: '
                        '%(error)s') % {'url': url, 'error': e}
                raise exceptions.SSLError(msg)
            except requests.exceptions.Timeout:
                msg = _('Request to %s timed out') % url
                raise exceptions.RequestTimeout(msg)
            except requests.exceptions.ConnectionError:
                msg = _('Unable to establish connection to %s') % url
                raise exceptions.ConnectionRefused(msg)
        except (exceptions.RequestTimeout, exceptions.ConnectionRefused) as e:
            if connect_retries <= 0:
                raise

            logger.info('Failure: %(e)s. Retrying in %(delay).1fs.',
                        {'e': e, 'delay': connect_retry_delay})
            time.sleep(connect_retry_delay)

            return self._send_request(
                url, method, redirect, log, logger,
                connect_retries=connect_retries - 1,
                connect_retry_delay=connect_retry_delay * 2,
                **kwargs)

        if log:
            self._http_log_response(resp, logger)

        if resp.status_code in self._REDIRECT_STATUSES:
            # be careful here in python True == 1 and False == 0
            if isinstance(redirect, bool):
                redirect_allowed = redirect
            else:
                redirect -= 1
                redirect_allowed = redirect >= 0

            if not redirect_allowed:
                return resp

            try:
                location = resp.headers['location']
            except KeyError:
                logger.warning("Failed to redirect request to %s as new "
                               "location was not provided.", resp.url)
            else:
                # NOTE(jamielennox): We don't pass through connect_retry_delay.
                # This request actually worked so we can reset the delay count.
                new_resp = self._send_request(
                    location, method, redirect, log, logger,
                    connect_retries=connect_retries,
                    **kwargs)

                if not isinstance(new_resp.history, list):
                    new_resp.history = list(new_resp.history)
                new_resp.history.insert(0, resp)
                resp = new_resp

        return resp

    def head(self, url, **kwargs):
        """Perform a HEAD request.

        This calls :py:meth:`.request()` with ``method`` set to ``HEAD``.

        """
        return self.request(url, 'HEAD', **kwargs)

    def get(self, url, **kwargs):
        """Perform a GET request.

        This calls :py:meth:`.request()` with ``method`` set to ``GET``.

        """
        return self.request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        """Perform a POST request.

        This calls :py:meth:`.request()` with ``method`` set to ``POST``.

        """
        return self.request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        """Perform a PUT request.

        This calls :py:meth:`.request()` with ``method`` set to ``PUT``.

        """
        return self.request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        """Perform a DELETE request.

        This calls :py:meth:`.request()` with ``method`` set to ``DELETE``.

        """
        return self.request(url, 'DELETE', **kwargs)

    def patch(self, url, **kwargs):
        """Perform a PATCH request.

        This calls :py:meth:`.request()` with ``method`` set to ``PATCH``.

        """
        return self.request(url, 'PATCH', **kwargs)

    @classmethod
    def construct(cls, kwargs):
        """Handle constructing a session from both old and new arguments.

        Support constructing a session from the old
        :py:class:`~keystoneclient.httpclient.HTTPClient` args as well as the
        new request-style arguments.

        .. warning::

            *DEPRECATED as of 1.7.0*: This function is purely for bridging the
            gap between older client arguments and the session arguments that
            they relate to. It is not intended to be used as a generic Session
            Factory. This function may be removed in the 2.0.0 release.

        This function purposefully modifies the input kwargs dictionary so that
        the remaining kwargs dict can be reused and passed on to other
        functions without session arguments.

        """
        warnings.warn(
            'Session.construct() is deprecated as of the 1.7.0 release  in '
            'favor of using session constructor and may be removed in the '
            '2.0.0 release.', DeprecationWarning)
        return cls._construct(kwargs)

    @classmethod
    def _construct(cls, kwargs):
        params = {}

        for attr in ('verify', 'cacert', 'cert', 'key', 'insecure',
                     'timeout', 'session', 'original_ip', 'user_agent'):
            try:
                params[attr] = kwargs.pop(attr)
            except KeyError:  # nosec(cjschaef): we are brute force
                # identifying possible attributes for kwargs
                pass

        return cls._make(**params)

    @classmethod
    def _make(cls, insecure=False, verify=None, cacert=None, cert=None,
              key=None, **kwargs):
        """Create a session with individual certificate parameters.

        Some parameters used to create a session don't lend themselves to be
        loaded from config/CLI etc. Create a session by converting those
        parameters into session __init__ parameters.
        """
        if verify is None:
            if insecure:
                verify = False
            else:
                verify = cacert or True

        if cert and key:
            warnings.warn(
                'Passing cert and key together is deprecated as of the 1.7.0 '
                'release in favor of the requests library form of having the '
                'cert and key as a tuple and may be removed in the 2.0.0 '
                'release.', DeprecationWarning)
            cert = (cert, key)

        return cls(verify=verify, cert=cert, **kwargs)

    def _auth_required(self, auth, msg):
        if not auth:
            auth = self.auth

        if not auth:
            raise exceptions.MissingAuthPlugin(msg)

        return auth

    def get_auth_headers(self, auth=None, **kwargs):
        """Return auth headers as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin
                     on the session. (optional)
        :type auth: :py:class:`keystoneclient.auth.base.BaseAuthPlugin`

        :raises keystoneclient.exceptions.AuthorizationFailure: if a new token
                                                                fetch fails.
        :raises keystoneclient.exceptions.MissingAuthPlugin: if a plugin is not
                                                             available.

        :returns: Authentication headers or None for failure.
        :rtype: dict
        """
        msg = _('An auth plugin is required to fetch a token')
        auth = self._auth_required(auth, msg)
        return auth.get_headers(self, **kwargs)

    @removals.remove(message='Use get_auth_headers instead.', version='1.7.0',
                     removal_version='2.0.0')
    def get_token(self, auth=None):
        """Return a token as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin
                     on the session. (optional)
        :type auth: :py:class:`keystoneclient.auth.base.BaseAuthPlugin`

        :raises keystoneclient.exceptions.AuthorizationFailure: if a new token
                                                                fetch fails.
        :raises keystoneclient.exceptions.MissingAuthPlugin: if a plugin is not
                                                             available.

        .. warning::

             This method is deprecated as of the 1.7.0 release in favor of
             :meth:`get_auth_headers` and may be removed in the 2.0.0 release.
             This method assumes that the only header that is used to
             authenticate a message is 'X-Auth-Token' which may not be correct.

        :returns: A valid token.
        :rtype: string
        """
        return (self.get_auth_headers(auth) or {}).get('X-Auth-Token')

    def get_endpoint(self, auth=None, **kwargs):
        """Get an endpoint as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin on
                     the session. (optional)
        :type auth: :py:class:`keystoneclient.auth.base.BaseAuthPlugin`

        :raises keystoneclient.exceptions.MissingAuthPlugin: if a plugin is not
                                                             available.

        :returns: An endpoint if available or None.
        :rtype: string
        """
        msg = _('An auth plugin is required to determine endpoint URL')
        auth = self._auth_required(auth, msg)
        return auth.get_endpoint(self, **kwargs)

    def get_auth_connection_params(self, auth=None, **kwargs):
        """Return auth connection params as provided by the auth plugin.

        An auth plugin may specify connection parameters to the request like
        providing a client certificate for communication.

        We restrict the values that may be returned from this function to
        prevent an auth plugin overriding values unrelated to connection
        parameters. The values that are currently accepted are:

        - `cert`: a path to a client certificate, or tuple of client
          certificate and key pair that are used with this request.
        - `verify`: a boolean value to indicate verifying SSL certificates
          against the system CAs or a path to a CA file to verify with.

        These values are passed to the requests library and further information
        on accepted values may be found there.

        :param auth: The auth plugin to use for tokens. Overrides the plugin
                     on the session. (optional)
        :type auth: keystoneclient.auth.base.BaseAuthPlugin

        :raises keystoneclient.exceptions.AuthorizationFailure: if a new token
                                                                fetch fails.
        :raises keystoneclient.exceptions.MissingAuthPlugin: if a plugin is not
                                                             available.
        :raises keystoneclient.exceptions.UnsupportedParameters: if the plugin
            returns a parameter that is not supported by this session.

        :returns: Authentication headers or None for failure.
        :rtype: dict
        """
        msg = _('An auth plugin is required to fetch connection params')
        auth = self._auth_required(auth, msg)
        params = auth.get_connection_params(self, **kwargs)

        # NOTE(jamielennox): There needs to be some consensus on what
        # parameters are allowed to be modified by the auth plugin here.
        # Ideally I think it would be only the send() parts of the request
        # flow. For now lets just allow certain elements.
        params_copy = params.copy()

        for arg in ('cert', 'verify'):
            try:
                kwargs[arg] = params_copy.pop(arg)
            except KeyError:  # nosec(cjschaef): we are brute force
                # identifying and removing values in params_copy
                pass

        if params_copy:
            raise exceptions.UnsupportedParameters(list(params_copy))

        return params

    def invalidate(self, auth=None):
        """Invalidate an authentication plugin.

        :param auth: The auth plugin to invalidate. Overrides the plugin on the
                     session. (optional)
        :type auth: :py:class:`keystoneclient.auth.base.BaseAuthPlugin`

        """
        msg = _('An auth plugin is required to validate')
        auth = self._auth_required(auth, msg)
        return auth.invalidate()

    def get_user_id(self, auth=None):
        """Return the authenticated user_id as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin
                     on the session. (optional)
        :type auth: keystoneclient.auth.base.BaseAuthPlugin

        :raises keystoneclient.exceptions.AuthorizationFailure:
            if a new token fetch fails.
        :raises keystoneclient.exceptions.MissingAuthPlugin:
            if a plugin is not available.

        :returns string: Current user_id or None if not supported by plugin.
        """
        msg = _('An auth plugin is required to get user_id')
        auth = self._auth_required(auth, msg)
        return auth.get_user_id(self)

    def get_project_id(self, auth=None):
        """Return the authenticated project_id as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin
                     on the session. (optional)
        :type auth: keystoneclient.auth.base.BaseAuthPlugin

        :raises keystoneclient.exceptions.AuthorizationFailure:
            if a new token fetch fails.
        :raises keystoneclient.exceptions.MissingAuthPlugin:
            if a plugin is not available.

        :returns string: Current project_id or None if not supported by plugin.
        """
        msg = _('An auth plugin is required to get project_id')
        auth = self._auth_required(auth, msg)
        return auth.get_project_id(self)

    @positional.classmethod()
    def get_conf_options(cls, deprecated_opts=None):
        """Get oslo_config options that are needed for a :py:class:`.Session`.

        These may be useful without being registered for config file generation
        or to manipulate the options before registering them yourself.

        The options that are set are:
            :cafile: The certificate authority filename.
            :certfile: The client certificate file to present.
            :keyfile: The key for the client certificate.
            :insecure: Whether to ignore SSL verification.
            :timeout: The max time to wait for HTTP connections.

        :param dict deprecated_opts: Deprecated options that should be included
             in the definition of new options. This should be a dict from the
             name of the new option to a list of oslo.DeprecatedOpts that
             correspond to the new option. (optional)

             For example, to support the ``ca_file`` option pointing to the new
             ``cafile`` option name::

                 old_opt = oslo_cfg.DeprecatedOpt('ca_file', 'old_group')
                 deprecated_opts={'cafile': [old_opt]}

        :returns: A list of oslo_config options.
        """
        if deprecated_opts is None:
            deprecated_opts = {}

        return [cfg.StrOpt('cafile',
                           deprecated_opts=deprecated_opts.get('cafile'),
                           help='PEM encoded Certificate Authority to use '
                                'when verifying HTTPs connections.'),
                cfg.StrOpt('certfile',
                           deprecated_opts=deprecated_opts.get('certfile'),
                           help='PEM encoded client certificate cert file'),
                cfg.StrOpt('keyfile',
                           deprecated_opts=deprecated_opts.get('keyfile'),
                           help='PEM encoded client certificate key file'),
                cfg.BoolOpt('insecure',
                            default=False,
                            deprecated_opts=deprecated_opts.get('insecure'),
                            help='Verify HTTPS connections.'),
                cfg.IntOpt('timeout',
                           deprecated_opts=deprecated_opts.get('timeout'),
                           help='Timeout value for http requests'),
                ]

    @positional.classmethod()
    def register_conf_options(cls, conf, group, deprecated_opts=None):
        """Register the oslo_config options that are needed for a session.

        The options that are set are:
            :cafile: The certificate authority filename.
            :certfile: The client certificate file to present.
            :keyfile: The key for the client certificate.
            :insecure: Whether to ignore SSL verification.
            :timeout: The max time to wait for HTTP connections.

        :param oslo_config.Cfg conf: config object to register with.
        :param string group: The ini group to register options in.
        :param dict deprecated_opts: Deprecated options that should be included
             in the definition of new options. This should be a dict from the
             name of the new option to a list of oslo.DeprecatedOpts that
             correspond to the new option. (optional)

             For example, to support the ``ca_file`` option pointing to the new
             ``cafile`` option name::

                 old_opt = oslo_cfg.DeprecatedOpt('ca_file', 'old_group')
                 deprecated_opts={'cafile': [old_opt]}

        :returns: The list of options that was registered.
        """
        opts = cls.get_conf_options(deprecated_opts=deprecated_opts)
        conf.register_group(cfg.OptGroup(group))
        conf.register_opts(opts, group=group)
        return opts

    @classmethod
    def load_from_conf_options(cls, conf, group, **kwargs):
        """Create a session object from an oslo_config object.

        The options must have been previously registered with
        register_conf_options.

        :param oslo_config.Cfg conf: config object to register with.
        :param string group: The ini group to register options in.
        :param dict kwargs: Additional parameters to pass to session
                            construction.
        :returns: A new session object.
        :rtype: :py:class:`.Session`
        """
        c = conf[group]

        kwargs['insecure'] = c.insecure
        kwargs['cacert'] = c.cafile
        if c.certfile and c.keyfile:
            kwargs['cert'] = (c.certfile, c.keyfile)
        kwargs['timeout'] = c.timeout

        return cls._make(**kwargs)

    @staticmethod
    def register_cli_options(parser):
        """Register the argparse arguments that are needed for a session.

        :param argparse.ArgumentParser parser: parser to add to.
        """
        parser.add_argument('--insecure',
                            default=False,
                            action='store_true',
                            help='Explicitly allow client to perform '
                                 '"insecure" TLS (https) requests. The '
                                 'server\'s certificate will not be verified '
                                 'against any certificate authorities. This '
                                 'option should be used with caution.')

        parser.add_argument('--os-cacert',
                            metavar='<ca-certificate>',
                            default=os.environ.get('OS_CACERT'),
                            help='Specify a CA bundle file to use in '
                                 'verifying a TLS (https) server certificate. '
                                 'Defaults to env[OS_CACERT].')

        parser.add_argument('--os-cert',
                            metavar='<certificate>',
                            default=os.environ.get('OS_CERT'),
                            help='Defaults to env[OS_CERT].')

        parser.add_argument('--os-key',
                            metavar='<key>',
                            default=os.environ.get('OS_KEY'),
                            help='Defaults to env[OS_KEY].')

        parser.add_argument('--timeout',
                            default=600,
                            type=_positive_non_zero_float,
                            metavar='<seconds>',
                            help='Set request timeout (in seconds).')

    @classmethod
    def load_from_cli_options(cls, args, **kwargs):
        """Create a :py:class:`.Session` object from CLI arguments.

        The CLI arguments must have been registered with
        :py:meth:`.register_cli_options`.

        :param Namespace args: result of parsed arguments.

        :returns: A new session object.
        :rtype: :py:class:`.Session`
        """
        kwargs['insecure'] = args.insecure
        kwargs['cacert'] = args.os_cacert
        if args.os_cert and args.os_key:
            kwargs['cert'] = (args.os_cert, args.os_key)
        kwargs['timeout'] = args.timeout

        return cls._make(**kwargs)


class TCPKeepAliveAdapter(requests.adapters.HTTPAdapter):
    """The custom adapter used to set TCP Keep-Alive on all connections.

    This Adapter also preserves the default behaviour of Requests which
    disables Nagle's Algorithm. See also:
    http://blogs.msdn.com/b/windowsazurestorage/archive/2010/06/25/nagle-s-algorithm-is-not-friendly-towards-small-requests.aspx
    """

    def init_poolmanager(self, *args, **kwargs):
        if 'socket_options' not in kwargs:
            socket_options = [
                # Keep Nagle's algorithm off
                (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
                # Turn on TCP Keep-Alive
                (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
            ]

            # Some operating systems (e.g., OSX) do not support setting
            # keepidle
            if hasattr(socket, 'TCP_KEEPIDLE'):
                socket_options += [
                    # Wait 60 seconds before sending keep-alive probes
                    (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                ]

            # TODO(claudiub): Windows does not contain the TCP_KEEPCNT and
            # TCP_KEEPINTVL socket attributes. Instead, it contains
            # SIO_KEEPALIVE_VALS, which can be set via ioctl, which should be
            # set once it is available in requests.
            # https://msdn.microsoft.com/en-us/library/dd877220%28VS.85%29.aspx
            if hasattr(socket, 'TCP_KEEPCNT'):
                socket_options += [
                    # Set the maximum number of keep-alive probes
                    (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 4)
                ]

            if hasattr(socket, 'TCP_KEEPINTVL'):
                socket_options += [
                    # Send keep-alive probes every 15 seconds
                    (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 15)
                ]

            # After waiting 60 seconds, and then sending a probe once every 15
            # seconds 4 times, these options should ensure that a connection
            # hands for no longer than 2 minutes before a ConnectionError is
            # raised.

            kwargs['socket_options'] = socket_options
        super(TCPKeepAliveAdapter, self).init_poolmanager(*args, **kwargs)
