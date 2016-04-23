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

"""
Produce keystone compliant structures for testing.

The generators in this directory produce keystone compliant structures for
use in testing.
They should be considered part of the public API because they may be relied
upon to generate test tokens for other clients. However they should never be
imported into the main client (keystoneclient or other). Because of this there
may be dependencies from this module on libraries that are only available in
testing.
"""

from keystoneclient.fixture.discovery import *  # noqa
from keystoneclient.fixture import exception
from keystoneclient.fixture import v2
from keystoneclient.fixture import v3


FixtureValidationError = exception.FixtureValidationError
V2Token = v2.Token
V3Token = v3.Token
V3FederationToken = v3.V3FederationToken

__all__ = ('DiscoveryList',
           'FixtureValidationError',
           'V2Discovery',
           'V3Discovery',
           'V2Token',
           'V3Token',
           'V3FederationToken',
           )
