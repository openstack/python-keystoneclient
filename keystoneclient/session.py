# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

import requests
import six

from keystoneclient import exceptions
from keystoneclient.openstack.common import jsonutils


USER_AGENT = 'python-keystoneclient'

_logger = logging.getLogger(__name__)


def request(url, method='GET', **kwargs):
    return Session().request(url, method=method, **kwargs)


class Session(object):

    user_agent = None

    REDIRECT_STATUSES = (301, 302, 303, 305, 307)
    DEFAULT_REDIRECT_LIMIT = 30

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
            session = requests.Session()

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

    def request(self, url, method, json=None, original_ip=None,
                user_agent=None, redirect=None, authenticated=None,
                **kwargs):
        """Send an HTTP request with the specified characteristics.

        Wrapper around `requests.Session.request` to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.

        Arguments that are not handled are passed through to the requests
        library.

        :param string url: Fully qualified URL of HTTP request
        :param string method: The http method to use. (eg. 'GET', 'POST')
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
            authenticated = self.auth is not None

        if authenticated:
            token = self.get_token()

            if not token:
                raise exceptions.AuthorizationFailure("No token Available")

            headers['X-Auth-Token'] = token

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

        string_parts = ['curl -i']

        # NOTE(jamielennox): None means let requests do its default validation
        # so we need to actually check that this is False.
        if self.verify is False:
            string_parts.append('--insecure')

        if method:
            string_parts.extend(['-X', method])

        string_parts.append(url)

        if headers:
            for header in six.iteritems(headers):
                string_parts.append('-H "%s: %s"' % header)

        try:
            string_parts.append("-d '%s'" % kwargs['data'])
        except KeyError:
            pass

        _logger.debug('REQ: %s', ' '.join(string_parts))

        # Force disable requests redirect handling. We will manage this below.
        kwargs['allow_redirects'] = False

        if redirect is None:
            redirect = self.redirect

        resp = self._send_request(url, method, redirect, **kwargs)

        # NOTE(jamielennox): we create a tuple here to be the same as what is
        # returned by the requests library.
        resp.history = tuple(resp.history)

        if resp.status_code >= 400:
            _logger.debug('Request returned failure status: %s',
                          resp.status_code)
            raise exceptions.from_response(resp, method, url)

        return resp

    def _send_request(self, url, method, redirect, **kwargs):
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
            raise exceptions.Timeout(msg)
        except requests.exceptions.ConnectionError:
            msg = 'Unable to establish connection to %s' % url
            raise exceptions.ConnectionError(msg)

        _logger.debug('RESP: [%s] %s\nRESP BODY: %s\n',
                      resp.status_code, resp.headers, resp.text)

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
                new_resp = self._send_request(location, method, redirect,
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
        verify = kwargs.pop('verify', None)
        cacert = kwargs.pop('cacert', None)
        cert = kwargs.pop('cert', None)
        key = kwargs.pop('key', None)
        insecure = kwargs.pop('insecure', False)

        if verify is None:
            if insecure:
                verify = False
            else:
                verify = cacert or True

        if cert and key:
            # passing cert and key together is deprecated in favour of the
            # requests lib form of having the cert and key as a tuple
            cert = (cert, key)

        return cls(verify=verify, cert=cert,
                   timeout=kwargs.pop('timeout', None),
                   session=kwargs.pop('session', None),
                   original_ip=kwargs.pop('original_ip', None),
                   user_agent=kwargs.pop('user_agent', None))

    def get_token(self):
        """Return a token as provided by the auth plugin."""
        if not self.auth:
            raise exceptions.MissingAuthPlugin("Token Required")

        return self.auth.get_token(self)
