# Copyright 2011 OpenStack LLC.
# Copyright 2011, Piston Cloud Computing, Inc.
# Copyright 2011 Nebula, Inc.
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from keystoneclient import exceptions


class ServiceCatalog(object):
    """Helper methods for dealing with a Keystone Service Catalog."""

    def __init__(self, resource_dict, region_name=None):
        self.catalog = resource_dict
        self.region_name = region_name

    def get_token(self):
        """Fetch token details from service catalog.

        Returns a dictionary containing the following::

        - `id`: Token's ID
        - `expires`: Token's expiration
        - `user_id`: Authenticated user's ID
        - `tenant_id`: Authorized project's ID

        """
        token = {'id': self.catalog['token']['id'],
                 'expires': self.catalog['token']['expires']}
        try:
            token['user_id'] = self.catalog['user']['id']
            token['tenant_id'] = self.catalog['token']['tenant']['id']
        except Exception:
            # just leave the tenant and user out if it doesn't exist
            pass
        return token

    def url_for(self, attr=None, filter_value=None,
                service_type='identity', endpoint_type='publicURL'):
        """Fetch an endpoint from the service catalog.

        Fetch the specified endpoint from the service catalog for
        a particular endpoint attribute. If no attribute is given, return
        the first endpoint of the specified type.

        Valid endpoint types: `publicURL`, `internalURL`, `adminURL`

        See tests for a sample service catalog.
        """
        catalog = self.catalog.get('serviceCatalog', [])

        if not catalog:
            raise exceptions.EmptyCatalog('The service catalog is empty.')

        for service in catalog:
            if service['type'] != service_type:
                continue

            endpoints = service['endpoints']
            for endpoint in endpoints:
                if self.region_name and \
                    endpoint.get('region') != self.region_name:
                    continue
                if not filter_value or endpoint.get(attr) == filter_value:
                    return endpoint[endpoint_type]

        raise exceptions.EndpointNotFound('%s endpoint for %s not found.' %
                                          (endpoint_type, service_type))

    def get_endpoints(self, service_type=None, endpoint_type=None):
        """Fetch and filter endpoints for the specified service(s).

        Returns endpoints for the specified service (or all) and
        that contain the specified type (or all).
        """
        sc = {}
        for service in self.catalog.get('serviceCatalog', []):
            if service_type and service_type != service['type']:
                continue
            sc[service['type']] = []
            for endpoint in service['endpoints']:
                if endpoint_type and endpoint_type not in endpoint.keys():
                    continue
                sc[service['type']].append(endpoint)
        return sc
