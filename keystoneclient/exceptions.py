# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from keystoneclient.apiclient.exceptions import *


class CertificateConfigError(Exception):
    """Error reading the certificate"""
    def __init__(self, output):
        self.output = output
        msg = ("Unable to load certificate. "
               "Ensure your system is configured properly.")
        super(CertificateConfigError, self).__init__(msg)


class ConnectionError(ClientException):
    """Something went wrong trying to connect to a server"""


class SSLError(ConnectionError):
    """An SSL error occurred."""


class Timeout(ClientException):
    """The request timed out."""


class DiscoveryFailure(ClientException):
    """Discovery of client versions failed."""


class VersionNotAvailable(DiscoveryFailure):
    """Discovery failed as the version you requested is not available."""
