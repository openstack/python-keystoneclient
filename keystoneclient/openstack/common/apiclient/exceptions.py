# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 Nebula, Inc.
# Copyright 2013 Alessio Ababilov
# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
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

########################################################################
#
# THIS MODULE IS DEPRECATED
#
# Please refer to
# https://etherpad.openstack.org/p/kilo-keystoneclient-library-proposals for
# the discussion leading to this deprecation.
#
# We recommend checking out the python-openstacksdk project
# (https://launchpad.net/python-openstacksdk) instead.
#
########################################################################

########################################################################
#
# THIS MODULE IS NOT SYNCED WITH OSLO-INCUBATOR.
# WE'RE JUST TRYING TO GET RID OF IT.
#
########################################################################

from keystoneclient.openstack.common._i18n import _

from keystoneclient import exceptions


"""Exception definitions."""

ClientException = exceptions.ClientException
ValidationError = exceptions.ValidationError
UnsupportedVersion = exceptions.UnsupportedVersion
CommandError = exceptions.CommandError
AuthorizationFailure = exceptions.AuthorizationFailure
ConnectionError = exceptions.ConnectionError
ConnectionRefused = exceptions.ConnectionRefused
AuthPluginOptionsMissing = exceptions.AuthPluginOptionsMissing
AuthSystemNotFound = exceptions.AuthSystemNotFound
NoUniqueMatch = exceptions.NoUniqueMatch
EndpointException = exceptions.EndpointException
EndpointNotFound = exceptions.EndpointNotFound
AmbiguousEndpoints = exceptions.AmbiguousEndpoints
HttpError = exceptions.HttpError
HTTPRedirection = exceptions.HTTPRedirection
HTTPClientError = exceptions.HTTPClientError
HttpServerError = exceptions.HttpServerError
MultipleChoices = exceptions.MultipleChoices
BadRequest = exceptions.BadRequest
Unauthorized = exceptions.Unauthorized
PaymentRequired = exceptions.PaymentRequired
Forbidden = exceptions.Forbidden
NotFound = exceptions.NotFound
MethodNotAllowed = exceptions.MethodNotAllowed
NotAcceptable = exceptions.NotAcceptable
ProxyAuthenticationRequired = exceptions.ProxyAuthenticationRequired
RequestTimeout = exceptions.RequestTimeout
Conflict = exceptions.Conflict
Gone = exceptions.Gone
LengthRequired = exceptions.LengthRequired
PreconditionFailed = exceptions.PreconditionFailed
RequestEntityTooLarge = exceptions.RequestEntityTooLarge
RequestUriTooLong = exceptions.RequestUriTooLong
UnsupportedMediaType = exceptions.UnsupportedMediaType
RequestedRangeNotSatisfiable = exceptions.RequestedRangeNotSatisfiable
ExpectationFailed = exceptions.ExpectationFailed
UnprocessableEntity = exceptions.UnprocessableEntity
InternalServerError = exceptions.InternalServerError
HttpNotImplemented = exceptions.HttpNotImplemented
BadGateway = exceptions.BadGateway
ServiceUnavailable = exceptions.ServiceUnavailable
GatewayTimeout = exceptions.GatewayTimeout
HttpVersionNotSupported = exceptions.HttpVersionNotSupported
from_response = exceptions.from_response
