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
"""
Exception definitions.
"""

#flake8: noqa
from keystoneclient.openstack.common.apiclient.exceptions import *

# NOTE(akurilin): This alias should be left here to support backwards
# compatibility until we are sure that usage of these exceptions in
# projects is correct.
ConnectionError = ConnectionRefused
HTTPNotImplemented = HttpNotImplemented
Timeout = RequestTimeout
HTTPError = HttpError


class CertificateConfigError(Exception):
    """Error reading the certificate"""
    def __init__(self, output):
        self.output = output
        msg = ("Unable to load certificate. "
               "Ensure your system is configured properly.")
        super(CertificateConfigError, self).__init__(msg)


class EmptyCatalog(EndpointNotFound):
    """The service catalog is empty."""
    pass


class SSLError(ConnectionRefused):
    """An SSL error occurred."""


class DiscoveryFailure(ClientException):
    """Discovery of client versions failed."""


class VersionNotAvailable(DiscoveryFailure):
    """Discovery failed as the version you requested is not available."""


class MissingAuthPlugin(ClientException):
    """An authenticated request is required but no plugin available."""


class NoMatchingPlugin(ClientException):
    """There were no auth plugins that could be created from the parameters
    provided."""


class InvalidResponse(ClientException):
    """The response from the server is not valid for this request."""

    def __init__(self, response):
        super(InvalidResponse, self).__init__()
        self.response = response
