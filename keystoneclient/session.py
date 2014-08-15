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
import logging
import os

from oslo.config import cfg
from oslo.utils import importutils
import requests
import six
from six.moves import urllib

from keystoneclient import exceptions
from keystoneclient.openstack.common import jsonutils
from keystoneclient import utils

osprofiler_web = importutils.try_import("osprofiler.web")

USER_AGENT = 'python-keystoneclient'

_logger = logging.getLogger(__name__)


def _positive_non_zero_float(argument_value):
    if argument_value is None:
        return None
    try:
        value = float(argument_value)
    except ValueError:
        msg = "%s must be a float" % argument_value
        raise argparse.ArgumentTypeError(msg)
    if value <= 0:
        msg = "%s must be greater than 0" % argument_value
        raise argparse.ArgumentTypeError(msg)
    return value


def request(url, method='GET', **kwargs):
    return Session().request(url, method=method, **kwargs)


class _FakeRequestSession(object):
    """This object is a temporary hack that should be removed later.

    Keystoneclient has a cyclical dependency with its managers which is
    preventing it from being cleaned up correctly. This is always bad but when
    we switched to doing connection pooling this object wasn't getting cleaned
    either and so we had left over TCP connections hanging around.

    Until we can fix the client cleanup we rollback the use of a requests
    session and do individual connections like we used to.
    """

    def request(self, *args, **kwargs):
        return requests.request(*args, **kwargs)


class Session(object):

    user_agent = None

    REDIRECT_STATUSES = (301, 302, 303, 305, 307)
    DEFAULT_REDIRECT_LIMIT = 30

    @utils.positional(2, enforcement=utils.positional.WARN)
    def __init__(self, auth=None, session=None, original_ip=None, verify=True,
                 cert=None, timeout=None, user_agent=None,
                 redirect=DEFAULT_REDIRECT_LIMIT):
        """Maintains client communication state and common functionality.

        As much as possible the parameters to this class reflect and are passed
        directly to the requests library.

        :param auth: An authentication plugin to authenticate the session with.
                     (optional, defaults to None)
        :param requests.Session session: A requests session object that can be
                                         used for issuing requests. (optional)
        :param string original_ip: The original IP of the requesting user
                                   which will be sent to identity service in a
                                   'Forwarded' header. (optional)
        :param verify: The verification arguments to pass to requests. These
                       are of the same form as requests expects, so True or
                       False to verify (or not) against system certificates or
                       a path to a bundle or CA certs to check against or None
                       for requests to attempt to locate and use certificates.
                       (optional, defaults to True)
        :param cert: A client certificate to pass to requests. These are of the
                     same form as requests expects. Either a single filename
                     containing both the certificate and key or a tuple
                     containing the path to the certificate then a path to the
                     key. (optional)
        :param float timeout: A timeout to pass to requests. This should be a
                              numerical value indicating some amount
                              (or fraction) of seconds or 0 for no timeout.
                              (optional, defaults to 0)
        :param string user_agent: A User-Agent header string to use for the
                                  request. If not provided a default is used.
                                  (optional, defaults to
                                  'python-keystoneclient')
        :param int/bool redirect: Controls the maximum number of redirections
                                  that can be followed by a request. Either an
                                  integer for a specific count or True/False
                                  for forever/never. (optional, default to 30)
        """
        if not session:
            session = _FakeRequestSession()

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

    @utils.positional()
    def _http_log_request(self, url, method=None, data=None,
                          json=None, headers=None):
        if not _logger.isEnabledFor(logging.DEBUG):
            # NOTE(morganfainberg): This whole debug section is expensive,
            # there is no need to do the work if we're not going to emit a
            # debug log.
            return

        def process_header(header):
            secure_headers = ('authorization', 'x-auth-token',
                              'x-subject-token',)
            if header[0].lower() in secure_headers:
                return (header[0], 'TOKEN_REDACTED')
            return header

        string_parts = ['REQ: curl -i']

        # NOTE(jamielennox): None means let requests do its default validation
        # so we need to actually check that this is False.
        if self.verify is False:
            string_parts.append('--insecure')

        if method:
            string_parts.extend(['-X', method])

        string_parts.append(url)

        if headers:
            for header in six.iteritems(headers):
                string_parts.append('-H "%s: %s"' % process_header(header))
        if json:
            data = jsonutils.dumps(json)
        if data:
            string_parts.append("-d '%s'" % data)

        _logger.debug(' '.join(string_parts))

    @utils.positional()
    def _http_log_response(self, response=None, json=None,
                           status_code=None, headers=None, text=None):
        if not _logger.isEnabledFor(logging.DEBUG):
            return

        if response:
            if not status_code:
                status_code = response.status_code
            if not headers:
                headers = response.headers
            if not text:
                text = response.text
        if json:
            text = jsonutils.dumps(json)

        string_parts = ['RESP:']

        if status_code:
            string_parts.append('[%s]' % status_code)
        if headers:
            string_parts.append('%s' % headers)
        if text:
            string_parts.append('\nRESP BODY: %s\n' % text)

        _logger.debug(' '.join(string_parts))

    @utils.positional(enforcement=utils.positional.WARN)
    def request(self, url, method, json=None, original_ip=None,
                user_agent=None, redirect=None, authenticated=None,
                endpoint_filter=None, auth=None, requests_auth=None,
                raise_exc=True, allow_reauth=True, log=True, **kwargs):
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
        :param bool authenticated: True if a token should be attached to this
                                   request, False if not or None for attach if
                                   an auth_plugin is available.
                                   (optional, defaults to None)
        :param dict endpoint_filter: Data to be provided to an auth plugin with
                                     which it should be able to determine an
                                     endpoint to use for this request. If not
                                     provided then URL is expected to be a
                                     fully qualified URL. (optional)
        :param auth: The auth plugin to use when authenticating this request.
                     This will override the plugin that is attached to the
                     session (if any). (optional)
        :type auth: :class:`keystoneclient.auth.base.BaseAuthPlugin`
        :param requests_auth: A requests library auth plugin that cannot be
                              passed via kwarg because the `auth` kwarg
                              collides with our own auth plugins. (optional)
        :type requests_auth: :class:`requests.auth.AuthBase`
        :param bool raise_exc: If True then raise an appropriate exception for
                               failed HTTP requests. If False then return the
                               request object. (optional, default True)
        :param bool allow_reauth: Allow fetching a new token and retrying the
                                  request on receiving a 401 Unauthorized
                                  response. (optional, default True)
        :param bool log: If True then log the request and response data to the
                         debug log. (optional, default True)
        :param kwargs: any other parameter that can be passed to
                       requests.Session.request (such as `headers`). Except:
                       'data' will be overwritten by the data in 'json' param.
                       'allow_redirects' is ignored as redirects are handled
                       by the session.

        :raises exceptions.ClientException: For connection failure, or to
                                            indicate an error response code.

        :returns: The response to the request.
        """

        headers = kwargs.setdefault('headers', dict())

        if authenticated is None:
            authenticated = bool(auth or self.auth)

        if authenticated:
            token = self.get_token(auth)

            if not token:
                raise exceptions.AuthorizationFailure("No token Available")

            headers['X-Auth-Token'] = token

        if osprofiler_web:
            headers.update(osprofiler_web.get_trace_id_headers())

        # if we are passed a fully qualified URL and an endpoint_filter we
        # should ignore the filter. This will make it easier for clients who
        # want to overrule the default endpoint_filter data added to all client
        # requests. We check fully qualified here by the presence of a host.
        url_data = urllib.parse.urlparse(url)
        if endpoint_filter and not url_data.netloc:
            base_url = self.get_endpoint(auth, **endpoint_filter)

            if not base_url:
                raise exceptions.EndpointNotFound()

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
                                   headers=headers)

        # Force disable requests redirect handling. We will manage this below.
        kwargs['allow_redirects'] = False

        if redirect is None:
            redirect = self.redirect

        resp = self._send_request(url, method, redirect, log, **kwargs)

        # handle getting a 401 Unauthorized response by invalidating the plugin
        # and then retrying the request. This is only tried once.
        if resp.status_code == 401 and authenticated and allow_reauth:
            if self.invalidate(auth):
                token = self.get_token(auth)
                if token:
                    headers['X-Auth-Token'] = token
                    resp = self._send_request(url, method, redirect, log,
                                              **kwargs)

        if raise_exc and resp.status_code >= 400:
            _logger.debug('Request returned failure status: %s',
                          resp.status_code)
            raise exceptions.from_response(resp, method, url)

        return resp

    def _send_request(self, url, method, redirect, log, **kwargs):
        # NOTE(jamielennox): We handle redirection manually because the
        # requests lib follows some browser patterns where it will redirect
        # POSTs as GETs for certain statuses which is not want we want for an
        # API. See: https://en.wikipedia.org/wiki/Post/Redirect/Get

        try:
            resp = self.session.request(method, url, **kwargs)
        except requests.exceptions.SSLError:
            msg = 'SSL exception connecting to %s' % url
            raise exceptions.SSLError(msg)
        except requests.exceptions.Timeout:
            msg = 'Request to %s timed out' % url
            raise exceptions.RequestTimeout(msg)
        except requests.exceptions.ConnectionError:
            msg = 'Unable to establish connection to %s' % url
            raise exceptions.ConnectionRefused(msg)

        if log:
            self._http_log_response(response=resp)

        if resp.status_code in self.REDIRECT_STATUSES:
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
                _logger.warn("Failed to redirect request to %s as new "
                             "location was not provided.", resp.url)
            else:
                new_resp = self._send_request(location, method, redirect, log,
                                              **kwargs)

                if not isinstance(new_resp.history, list):
                    new_resp.history = list(new_resp.history)
                new_resp.history.insert(0, resp)
                resp = new_resp

        return resp

    def head(self, url, **kwargs):
        return self.request(url, 'HEAD', **kwargs)

    def get(self, url, **kwargs):
        return self.request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self.request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self.request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self.request(url, 'DELETE', **kwargs)

    def patch(self, url, **kwargs):
        return self.request(url, 'PATCH', **kwargs)

    @classmethod
    def construct(cls, kwargs):
        """Handles constructing a session from the older HTTPClient args as
        well as the new request style arguments.

        *DEPRECATED*: This function is purely for bridging the gap between
        older client arguments and the session arguments that they relate to.
        It is not intended to be used as a generic Session Factory.

        This function purposefully modifies the input kwargs dictionary so that
        the remaining kwargs dict can be reused and passed on to other
        functionswithout session arguments.

        """
        params = {}

        for attr in ('verify', 'cacert', 'cert', 'key', 'insecure',
                     'timeout', 'session', 'original_ip', 'user_agent'):
            try:
                params[attr] = kwargs.pop(attr)
            except KeyError:
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
            # passing cert and key together is deprecated in favour of the
            # requests lib form of having the cert and key as a tuple
            cert = (cert, key)

        return cls(verify=verify, cert=cert, **kwargs)

    def get_token(self, auth=None):
        """Return a token as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin
                     on the session. (optional)
        :type auth: :class:`keystoneclient.auth.base.BaseAuthPlugin`

        :raises AuthorizationFailure: if a new token fetch fails.

        :returns string: A valid token.
        """
        if not auth:
            auth = self.auth

        if not auth:
            raise exceptions.MissingAuthPlugin("Token Required")

        try:
            return auth.get_token(self)
        except exceptions.HttpError as exc:
            raise exceptions.AuthorizationFailure("Authentication failure: "
                                                  "%s" % exc)

    def get_endpoint(self, auth=None, **kwargs):
        """Get an endpoint as provided by the auth plugin.

        :param auth: The auth plugin to use for token. Overrides the plugin on
                     the session. (optional)
        :type auth: :class:`keystoneclient.auth.base.BaseAuthPlugin`

        :raises MissingAuthPlugin: if a plugin is not available.

        :returns string: An endpoint if available or None.
        """
        if not auth:
            auth = self.auth

        if not auth:
            raise exceptions.MissingAuthPlugin('An auth plugin is required to '
                                               'determine the endpoint URL.')

        return auth.get_endpoint(self, **kwargs)

    def invalidate(self, auth=None):
        """Invalidate an authentication plugin.
        """
        if not auth:
            auth = self.auth

        if not auth:
            msg = 'Auth plugin not available to invalidate'
            raise exceptions.MissingAuthPlugin(msg)

        return auth.invalidate()

    @utils.positional.classmethod()
    def get_conf_options(cls, deprecated_opts=None):
        """Get the oslo.config options that are needed for a session.

        These may be useful without being registered for config file generation
        or to manipulate the options before registering them yourself.

        The options that are set are:
            :cafile: The certificate authority filename.
            :certfile: The client certificate file to present.
            :keyfile: The key for the client certificate.
            :insecure: Whether to ignore SSL verification.
            :timeout: The max time to wait for HTTP connections.

        :param dict deprecated_opts: Deprecated options that should be included
             in the definition of new options. This should be a dictionary from
             the name of the new option to a list of oslo.DeprecatedOpts that
             correspond to the new option. (optional)

             Example to support the 'ca_file' option pointing to the new
             'cafile' option name::

                 old_opt = oslo.cfg.DeprecatedOpt('ca_file', 'old_group')
                 deprecated_opts={'cafile': [old_opt]}

        :returns: A list of oslo.config options.
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

    @utils.positional.classmethod()
    def register_conf_options(cls, conf, group, deprecated_opts=None):
        """Register the oslo.config options that are needed for a session.

        The options that are set are:
            :cafile: The certificate authority filename.
            :certfile: The client certificate file to present.
            :keyfile: The key for the client certificate.
            :insecure: Whether to ignore SSL verification.
            :timeout: The max time to wait for HTTP connections.

        :param oslo.config.Cfg conf: config object to register with.
        :param string group: The ini group to register options in.
        :param dict deprecated_opts: Deprecated options that should be included
             in the definition of new options. This should be a dictionary from
             the name of the new option to a list of oslo.DeprecatedOpts that
             correspond to the new option. (optional)

             Example to support the 'ca_file' option pointing to the new
             'cafile' option name::

                 old_opt = oslo.cfg.DeprecatedOpt('ca_file', 'old_group')
                 deprecated_opts={'cafile': [old_opt]}

        :returns: The list of options that was registered.
        """
        opts = cls.get_conf_options(deprecated_opts=deprecated_opts)
        conf.register_group(cfg.OptGroup(group))
        conf.register_opts(opts, group=group)
        return opts

    @classmethod
    def load_from_conf_options(cls, conf, group, **kwargs):
        """Create a session object from an oslo.config object.

        The options must have been previously registered with
        register_conf_options.

        :param oslo.config.Cfg conf: config object to register with.
        :param string group: The ini group to register options in.
        :param dict kwargs: Additional parameters to pass to session
                            construction.
        :returns: A new session object.
        """
        c = conf[group]

        kwargs['insecure'] = c.insecure
        kwargs['cacert'] = c.cafile
        kwargs['cert'] = c.certfile
        kwargs['key'] = c.keyfile
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
        """Create a session object from CLI arguments.

        The CLI arguments must have been registered with register_cli_options.

        :param Namespace args: result of parsed arguments.

        :returns: A new session object.
        """
        kwargs['insecure'] = args.insecure
        kwargs['cacert'] = args.os_cacert
        kwargs['cert'] = args.os_cert
        kwargs['key'] = args.os_key
        kwargs['timeout'] = args.timeout

        return cls._make(**kwargs)
