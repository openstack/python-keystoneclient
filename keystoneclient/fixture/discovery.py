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

from keystoneauth1.fixture import discovery


__all__ = ('DiscoveryList',
           'V2Discovery',
           'V3Discovery',
           )


V2Discovery = discovery.V2Discovery
"""A Version element for a V2 identity service endpoint.

An alias of :py:exc:`keystoneauth1.fixture.discovery.V2Discovery`
"""

V3Discovery = discovery.V3Discovery
"""A Version element for a V3 identity service endpoint.

An alias of :py:exc:`keystoneauth1.fixture.discovery.V3Discovery`
"""

DiscoveryList = discovery.DiscoveryList
"""A List of version elements.

An alias of :py:exc:`keystoneauth1.fixture.discovery.DiscoveryList`
"""
