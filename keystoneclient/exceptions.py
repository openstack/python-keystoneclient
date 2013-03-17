# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 Nebula, Inc.
"""
Exception definitions.
"""


class CommandError(Exception):
    pass


class ValidationError(Exception):
    pass


class AuthorizationFailure(Exception):
    pass


class NoTokenLookupException(Exception):
    """This form of authentication does not support looking up
       endpoints from an existing token."""
    pass


class EndpointNotFound(Exception):
    """Could not find Service or Region in Service Catalog."""
    pass


class EmptyCatalog(Exception):
    """ The service catalog is empty. """
    pass


class NoUniqueMatch(Exception):
    """Unable to find unique resource"""
    pass


class ClientException(Exception):
    """
    The base exception class for all exceptions this library raises.
    """
    def __init__(self, code, message=None, details=None):
        self.code = code
        self.message = message or self.__class__.message
        self.details = details

    def __str__(self):
        return "%s (HTTP %s)" % (self.message, self.code)


class BadRequest(ClientException):
    """
    HTTP 400 - Bad request: you sent some malformed data.
    """
    http_status = 400
    message = "Bad request"


class Unauthorized(ClientException):
    """
    HTTP 401 - Unauthorized: bad credentials.
    """
    http_status = 401
    message = "Unauthorized"


class Forbidden(ClientException):
    """
    HTTP 403 - Forbidden: your credentials don't give you access to this
    resource.
    """
    http_status = 403
    message = "Forbidden"


class NotFound(ClientException):
    """
    HTTP 404 - Not found
    """
    http_status = 404
    message = "Not found"


class MethodNotAllowed(ClientException):
    """
    HTTP 405 - Method not allowed
    """
    http_status = 405
    message = "Method not allowed"


class Conflict(ClientException):
    """
    HTTP 409 - Conflict
    """
    http_status = 409
    message = "Conflict"


class OverLimit(ClientException):
    """
    HTTP 413 - Over limit: you're over the API limits for this time period.
    """
    http_status = 413
    message = "Over limit"


# NotImplemented is a python keyword.
class HTTPNotImplemented(ClientException):
    """
    HTTP 501 - Not Implemented: the server does not support this operation.
    """
    http_status = 501
    message = "Not Implemented"


class ServiceUnavailable(ClientException):
    """
    HTTP 503 - Service Unavailable: The server is currently unavailable.
    """
    http_status = 503
    message = "Service Unavailable"


# In Python 2.4 Exception is old-style and thus doesn't have a __subclasses__()
# so we can do this:
#     _code_map = dict((c.http_status, c)
#                      for c in ClientException.__subclasses__())
#
# Instead, we have to hardcode it:
_code_map = dict((c.http_status, c) for c in [BadRequest,
                                              Unauthorized,
                                              Forbidden,
                                              NotFound,
                                              MethodNotAllowed,
                                              OverLimit,
                                              HTTPNotImplemented,
                                              ServiceUnavailable])


def from_response(response, body):
    """
    Return an instance of an ClientException or subclass
    based on an requests response.

    Usage::

        resp = requests.request(...)
        if resp.status_code != 200:
            raise exception_from_response(resp, resp.text)
    """
    cls = _code_map.get(response.status_code, ClientException)
    if body:
        if hasattr(body, 'keys'):
            error = body[body.keys()[0]]
            message = error.get('message', None)
            details = error.get('details', None)
        else:
            # If we didn't get back a properly formed error message we
            # probably couldn't communicate with Keystone at all.
            message = "Unable to communicate with identity service: %s." % body
            details = None
        return cls(code=response.status_code, message=message, details=details)
    else:
        return cls(code=response.status_code)
