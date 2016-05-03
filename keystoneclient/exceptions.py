# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 Nebula, Inc.
#
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
"""Exception definitions."""

from keystoneauth1 import exceptions as _exc

from keystoneclient.i18n import _


ClientException = _exc.ClientException
"""The base exception class for all exceptions this library raises.

An alias of :py:exc:`keystoneauth1.exceptions.base.ClientException`
"""

ConnectionError = _exc.ConnectionError
"""Cannot connect to API service.

An alias of :py:exc:`keystoneauth1.exceptions.connection.ConnectionError`
"""

ConnectionRefused = _exc.ConnectFailure
"""Connection refused while trying to connect to API service.

An alias of :py:exc:`keystoneauth1.exceptions.connection.ConnectFailure`
"""

SSLError = _exc.SSLError
"""An SSL error occurred.

An alias of :py:exc:`keystoneauth1.exceptions.connection.SSLError`
"""

AuthorizationFailure = _exc.AuthorizationFailure
"""Cannot authorize API client.

An alias of :py:exc:`keystoneauth1.exceptions.auth.AuthorizationFailure`
"""


class ValidationError(ClientException):
    """Error in validation on API client side."""

    pass


class UnsupportedVersion(ClientException):
    """User is trying to use an unsupported version of the API."""

    pass


class CommandError(ClientException):
    """Error in CLI tool."""

    pass


class AuthPluginOptionsMissing(AuthorizationFailure):
    """Auth plugin misses some options."""

    def __init__(self, opt_names):
        super(AuthPluginOptionsMissing, self).__init__(
            _("Authentication failed. Missing options: %s") %
            ", ".join(opt_names))
        self.opt_names = opt_names


class AuthSystemNotFound(AuthorizationFailure):
    """User has specified an AuthSystem that is not installed."""

    def __init__(self, auth_system):
        super(AuthSystemNotFound, self).__init__(
            _("AuthSystemNotFound: %r") % auth_system)
        self.auth_system = auth_system


class NoUniqueMatch(ClientException):
    """Multiple entities found instead of one."""

    pass


EndpointException = _exc.CatalogException
"""Something is rotten in Service Catalog.

An alias of :py:exc:`keystoneauth1.exceptions.catalog.CatalogException`
"""

EndpointNotFound = _exc.EndpointNotFound
"""Could not find requested endpoint in Service Catalog.

An alias of :py:exc:`keystoneauth1.exceptions.catalog.EndpointNotFound`
"""


class AmbiguousEndpoints(EndpointException):
    """Found more than one matching endpoint in Service Catalog."""

    def __init__(self, endpoints=None):
        super(AmbiguousEndpoints, self).__init__(
            _("AmbiguousEndpoints: %r") % endpoints)
        self.endpoints = endpoints


HttpError = _exc.HttpError
"""The base exception class for all HTTP exceptions.

An alias of :py:exc:`keystoneauth1.exceptions.http.HttpError`
"""

HTTPClientError = _exc.HTTPClientError
"""Client-side HTTP error.

Exception for cases in which the client seems to have erred.
An alias of :py:exc:`keystoneauth1.exceptions.http.HTTPClientError`
"""

HttpServerError = _exc.HttpServerError
"""Server-side HTTP error.

Exception for cases in which the server is aware that it has
erred or is incapable of performing the request.
An alias of :py:exc:`keystoneauth1.exceptions.http.HttpServerError`
"""


class HTTPRedirection(HttpError):
    """HTTP Redirection."""

    message = _("HTTP Redirection")


class MultipleChoices(HTTPRedirection):
    """HTTP 300 - Multiple Choices.

    Indicates multiple options for the resource that the client may follow.
    """

    http_status = 300
    message = _("Multiple Choices")


BadRequest = _exc.BadRequest
"""HTTP 400 - Bad Request.

The request cannot be fulfilled due to bad syntax.
An alias of :py:exc:`keystoneauth1.exceptions.http.BadRequest`
"""

Unauthorized = _exc.Unauthorized
"""HTTP 401 - Unauthorized.

Similar to 403 Forbidden, but specifically for use when authentication
is required and has failed or has not yet been provided.
An alias of :py:exc:`keystoneauth1.exceptions.http.Unauthorized`
"""

PaymentRequired = _exc.PaymentRequired
"""HTTP 402 - Payment Required.

Reserved for future use.
An alias of :py:exc:`keystoneauth1.exceptions.http.PaymentRequired`
"""

Forbidden = _exc.Forbidden
"""HTTP 403 - Forbidden.

The request was a valid request, but the server is refusing to respond
to it.
An alias of :py:exc:`keystoneauth1.exceptions.http.Forbidden`
"""

NotFound = _exc.NotFound
"""HTTP 404 - Not Found.

The requested resource could not be found but may be available again
in the future.
An alias of :py:exc:`keystoneauth1.exceptions.http.NotFound`
"""

MethodNotAllowed = _exc.MethodNotAllowed
"""HTTP 405 - Method Not Allowed.

A request was made of a resource using a request method not supported
by that resource.
An alias of :py:exc:`keystoneauth1.exceptions.http.MethodNotAllowed`
"""

NotAcceptable = _exc.NotAcceptable
"""HTTP 406 - Not Acceptable.

The requested resource is only capable of generating content not
acceptable according to the Accept headers sent in the request.
An alias of :py:exc:`keystoneauth1.exceptions.http.NotAcceptable`
"""

ProxyAuthenticationRequired = _exc.ProxyAuthenticationRequired
"""HTTP 407 - Proxy Authentication Required.

The client must first authenticate itself with the proxy.
An alias of :py:exc:`keystoneauth1.exceptions.http.ProxyAuthenticationRequired`
"""

RequestTimeout = _exc.RequestTimeout
"""HTTP 408 - Request Timeout.

The server timed out waiting for the request.
An alias of :py:exc:`keystoneauth1.exceptions.http.RequestTimeout`
"""

Conflict = _exc.Conflict
"""HTTP 409 - Conflict.

Indicates that the request could not be processed because of conflict
in the request, such as an edit conflict.
An alias of :py:exc:`keystoneauth1.exceptions.http.Conflict`
"""

Gone = _exc.Gone
"""HTTP 410 - Gone.

Indicates that the resource requested is no longer available and will
not be available again.
An alias of :py:exc:`keystoneauth1.exceptions.http.Gone`
"""

LengthRequired = _exc.LengthRequired
"""HTTP 411 - Length Required.

The request did not specify the length of its content, which is
required by the requested resource.
An alias of :py:exc:`keystoneauth1.exceptions.http.LengthRequired`
"""

PreconditionFailed = _exc.PreconditionFailed
"""HTTP 412 - Precondition Failed.

The server does not meet one of the preconditions that the requester
put on the request.
An alias of :py:exc:`keystoneauth1.exceptions.http.PreconditionFailed`
"""

RequestEntityTooLarge = _exc.RequestEntityTooLarge
"""HTTP 413 - Request Entity Too Large.

The request is larger than the server is willing or able to process.
An alias of :py:exc:`keystoneauth1.exceptions.http.RequestEntityTooLarge`
"""

RequestUriTooLong = _exc.RequestUriTooLong
"""HTTP 414 - Request-URI Too Long.

The URI provided was too long for the server to process.
An alias of :py:exc:`keystoneauth1.exceptions.http.RequestUriTooLong`
"""

UnsupportedMediaType = _exc.UnsupportedMediaType
"""HTTP 415 - Unsupported Media Type.

The request entity has a media type which the server or resource does
not support.
An alias of :py:exc:`keystoneauth1.exceptions.http.UnsupportedMediaType`
"""

RequestedRangeNotSatisfiable = _exc.RequestedRangeNotSatisfiable
"""HTTP 416 - Requested Range Not Satisfiable.

The client has asked for a portion of the file, but the server cannot
supply that portion.
An alias of
:py:exc:`keystoneauth1.exceptions.http.RequestedRangeNotSatisfiable`
"""

ExpectationFailed = _exc.ExpectationFailed
"""HTTP 417 - Expectation Failed.

The server cannot meet the requirements of the Expect request-header field.
An alias of :py:exc:`keystoneauth1.exceptions.http.ExpectationFailed`
"""

UnprocessableEntity = _exc.UnprocessableEntity
"""HTTP 422 - Unprocessable Entity.

The request was well-formed but was unable to be followed due to semantic
errors.
An alias of :py:exc:`keystoneauth1.exceptions.http.UnprocessableEntity`
"""

InternalServerError = _exc.InternalServerError
"""HTTP 500 - Internal Server Error.

A generic error message, given when no more specific message is suitable.
An alias of :py:exc:`keystoneauth1.exceptions.http.InternalServerError`
"""

HttpNotImplemented = _exc.HttpNotImplemented
"""HTTP 501 - Not Implemented.

The server either does not recognize the request method, or it lacks
the ability to fulfill the request.
An alias of :py:exc:`keystoneauth1.exceptions.http.HttpNotImplemented`
"""

BadGateway = _exc.BadGateway
"""HTTP 502 - Bad Gateway.

The server was acting as a gateway or proxy and received an invalid
response from the upstream server.
An alias of :py:exc:`keystoneauth1.exceptions.http.BadGateway`
"""

ServiceUnavailable = _exc.ServiceUnavailable
"""HTTP 503 - Service Unavailable.

The server is currently unavailable.
An alias of :py:exc:`keystoneauth1.exceptions.http.ServiceUnavailable`
"""

GatewayTimeout = _exc.GatewayTimeout
"""HTTP 504 - Gateway Timeout.

The server was acting as a gateway or proxy and did not receive a timely
response from the upstream server.
An alias of :py:exc:`keystoneauth1.exceptions.http.GatewayTimeout`
"""

HttpVersionNotSupported = _exc.HttpVersionNotSupported
"""HTTP 505 - HttpVersion Not Supported.

The server does not support the HTTP protocol version used in the request.
An alias of :py:exc:`keystoneauth1.exceptions.http.HttpVersionNotSupported`
"""

from_response = _exc.from_response
"""Return an instance of :class:`HttpError` or subclass based on response.

An alias of :py:func:`keystoneauth1.exceptions.http.from_response`
"""


# NOTE(akurilin): This alias should be left here to support backwards
# compatibility until we are sure that usage of these exceptions in
# projects is correct.
HTTPNotImplemented = HttpNotImplemented
Timeout = RequestTimeout
HTTPError = HttpError


class CertificateConfigError(Exception):
    """Error reading the certificate."""

    def __init__(self, output):
        self.output = output
        msg = _('Unable to load certificate.')
        super(CertificateConfigError, self).__init__(msg)


class CMSError(Exception):
    """Error reading the certificate."""

    def __init__(self, output):
        self.output = output
        msg = _('Unable to sign or verify data.')
        super(CMSError, self).__init__(msg)

EmptyCatalog = _exc.EmptyCatalog
"""The service catalog is empty.

An alias of :py:exc:`keystoneauth1.exceptions.catalog.EmptyCatalog`
"""

DiscoveryFailure = _exc.DiscoveryFailure
"""Discovery of client versions failed.

An alias of :py:exc:`keystoneauth1.exceptions.discovery.DiscoveryFailure`
"""

VersionNotAvailable = _exc.VersionNotAvailable
"""Discovery failed as the version you requested is not available.

An alias of :py:exc:`keystoneauth1.exceptions.discovery.VersionNotAvailable`
"""


class MethodNotImplemented(ClientException):
    """Method not implemented by the keystoneclient API."""

MissingAuthPlugin = _exc.MissingAuthPlugin
"""An authenticated request is required but no plugin available.

An alias of :py:exc:`keystoneauth1.exceptions.auth_plugins.MissingAuthPlugin`
"""

NoMatchingPlugin = _exc.NoMatchingPlugin
"""There were no auth plugins that could be created from the parameters
provided.

An alias of :py:exc:`keystoneauth1.exceptions.auth_plugins.NoMatchingPlugin`
"""


class UnsupportedParameters(ClientException):
    """A parameter that was provided or returned is not supported.

    :param list(str) names: Names of the unsupported parameters.

    .. py:attribute:: names

        Names of the unsupported parameters.
    """

    def __init__(self, names):
        self.names = names

        m = _('The following parameters were given that are unsupported: %s')
        super(UnsupportedParameters, self).__init__(m % ', '.join(self.names))


class InvalidResponse(ClientException):
    """The response from the server is not valid for this request."""

    def __init__(self, response):
        super(InvalidResponse, self).__init__()
        self.response = response
