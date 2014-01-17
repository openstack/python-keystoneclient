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

from keystoneclient import discover
from keystoneclient import httpclient


# Using client.HTTPClient is deprecated. Use httpclient.HTTPClient instead.
HTTPClient = httpclient.HTTPClient


def Client(version=None, unstable=False, **kwargs):
    """Factory function to create a new identity service client.

    :param tuple version: The required version of the identity API. If
                          specified the client will be selected such that the
                          major version is equivalent and an endpoint provides
                          at least the specified minor version. For example to
                          specify the 3.1 API use (3, 1).
    :param bool unstable: Accept endpoints not marked as 'stable'. (optional)
    :param kwargs: Additional arguments are passed through to the client
                   that is being created.
    :returns: New keystone client object
              (keystoneclient.v2_0.Client or keystoneclient.v3.Client).

    :raises: DiscoveryFailure if the server's response is invalid
    :raises: VersionNotAvailable if a suitable client cannot be found.
    """

    return discover.Discover(**kwargs).create_client(version=version,
                                                     unstable=unstable)
