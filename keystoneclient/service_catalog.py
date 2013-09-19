# Copyright 2011 OpenStack Foundation
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

    @classmethod
    def factory(cls, resource_dict, token=None, region_name=None):
        """Create ServiceCatalog object given a auth token."""
        if ServiceCatalogV3.is_valid(resource_dict):
            return ServiceCatalogV3(token, resource_dict, region_name)
        elif ServiceCatalogV2.is_valid(resource_dict):
            return ServiceCatalogV2(resource_dict, region_name)
        else:
            raise NotImplementedError('Unrecognized auth response')

    def get_token(self):
        """Fetch token details from service catalog.

        Returns a dictionary containing the following::

        - `id`: Token's ID
        - `expires`: Token's expiration
        - `user_id`: Authenticated user's ID
        - `tenant_id`: Authorized project's ID
        - `domain_id`: Authorized domain's ID

        """
        raise NotImplementedError()

    def get_endpoints(self, service_type=None, endpoint_type=None):
        """Fetch and filter endpoints for the specified service(s).

        Returns endpoints for the specified service (or all) and
        that contain the specified type (or all).
        """
        raise NotImplementedError()

    def get_urls(self, attr=None, filter_value=None,
                 service_type='identity', endpoint_type='publicURL'):
        """Fetch endpoint urls from the service catalog.

        Fetch the endpoints from the service catalog for a particular
        endpoint attribute. If no attribute is given, return the first
        endpoint of the specified type.

        :param string attr: Endpoint attribute name.
        :param string filter_value: Endpoint attribute value.
        :param string service_type: Service type of the endpoint.
        :param string endpoint_type: Type of endpoint.
                                     Possible values: public or publicURL,
                                         internal or internalURL,
                                         admin or adminURL
        :param string region_name: Region of the endpoint.

        :returns: tuple of urls or None (if no match found)
        """
        raise NotImplementedError()

    def url_for(self, attr=None, filter_value=None,
                service_type='identity', endpoint_type='publicURL'):
        """Fetch an endpoint from the service catalog.

        Fetch the specified endpoint from the service catalog for
        a particular endpoint attribute. If no attribute is given, return
        the first endpoint of the specified type.

        Valid endpoint types: `public` or `publicURL`,
                              `internal` or `internalURL`,
                              `admin` or 'adminURL`
        """
        raise NotImplementedError()

    def get_data(self):
        """Get the raw catalog structure.

        Get the version dependant catalog structure as it is presented within
        the resource.

        :returns: dict containing raw catalog data or None
        """
        raise NotImplementedError()


class ServiceCatalogV2(ServiceCatalog):
    """An object for encapsulating the service catalog using raw v2 auth token
    from Keystone.
    """

    def __init__(self, resource_dict, region_name=None):
        self.catalog = resource_dict
        self.region_name = region_name

    @classmethod
    def is_valid(cls, resource_dict):
        # This class is also used for reading token info of an unscoped token.
        # Unscoped token does not have 'serviceCatalog' in V2, checking this
        # will not work. Use 'token' attribute instead.
        return 'token' in resource_dict

    def get_data(self):
        return self.catalog.get('serviceCatalog')

    def get_token(self):
        token = {'id': self.catalog['token']['id'],
                 'expires': self.catalog['token']['expires']}
        try:
            token['user_id'] = self.catalog['user']['id']
            token['tenant_id'] = self.catalog['token']['tenant']['id']
        except Exception:
            # just leave the tenant and user out if it doesn't exist
            pass
        return token

    def get_endpoints(self, service_type=None, endpoint_type=None):
        if endpoint_type and 'URL' not in endpoint_type:
            endpoint_type = endpoint_type + 'URL'

        sc = {}
        for service in (self.get_data() or []):
            if service_type and service_type != service['type']:
                continue
            sc[service['type']] = []
            for endpoint in service['endpoints']:
                if endpoint_type and endpoint_type not in endpoint.keys():
                    continue
                sc[service['type']].append(endpoint)
        return sc

    def get_urls(self, attr=None, filter_value=None,
                 service_type='identity', endpoint_type='publicURL'):
        sc_endpoints = self.get_endpoints(service_type=service_type,
                                          endpoint_type=endpoint_type)
        endpoints = sc_endpoints.get(service_type)
        if not endpoints:
            return

        if endpoint_type and 'URL' not in endpoint_type:
            endpoint_type = endpoint_type + 'URL'

        return tuple(endpoint[endpoint_type]
                     for endpoint in endpoints
                     if (endpoint_type in endpoint
                         and (not self.region_name
                              or endpoint.get('region') == self.region_name)
                         and (not filter_value
                              or endpoint.get(attr) == filter_value)))

    def url_for(self, attr=None, filter_value=None,
                service_type='identity', endpoint_type='publicURL'):
        catalog = self.get_data()

        if not catalog:
            raise exceptions.EmptyCatalog('The service catalog is empty.')

        if 'URL' not in endpoint_type:
            endpoint_type = endpoint_type + 'URL'

        for service in catalog:
            if service['type'] != service_type:
                continue

            endpoints = service['endpoints']
            for endpoint in endpoints:
                if (self.region_name and
                        endpoint.get('region') != self.region_name):
                    continue
                if not filter_value or endpoint.get(attr) == filter_value:
                    return endpoint[endpoint_type]

        raise exceptions.EndpointNotFound('%s endpoint for %s not found.' %
                                          (endpoint_type, service_type))


class ServiceCatalogV3(ServiceCatalog):
    """An object for encapsulating the service catalog using raw v3 auth token
    from Keystone.
    """

    def __init__(self, token, resource_dict, region_name=None):
        self._auth_token = token
        self.catalog = resource_dict
        self.region_name = region_name

    @classmethod
    def is_valid(cls, resource_dict):
        # This class is also used for reading token info of an unscoped token.
        # Unscoped token does not have 'catalog', checking this
        # will not work. Use 'methods' attribute instead.
        return 'methods' in resource_dict

    def get_data(self):
        return self.catalog.get('catalog')

    def get_token(self):
        token = {'id': self._auth_token,
                 'expires': self.catalog['expires_at']}
        try:
            token['user_id'] = self.catalog['user']['id']
            domain = self.catalog.get('domain')
            if domain:
                token['domain_id'] = domain['id']
            project = self.catalog.get('project')
            if project:
                token['tenant_id'] = project['id']
        except Exception:
            # just leave the domain, project and user out if it doesn't exist
            pass
        return token

    def get_endpoints(self, service_type=None, endpoint_type=None):
        if endpoint_type:
            endpoint_type = endpoint_type.rstrip('URL')
        sc = {}
        for service in (self.get_data() or []):
            if service_type and service_type != service['type']:
                continue
            sc[service['type']] = []
            for endpoint in service['endpoints']:
                if endpoint_type and endpoint_type != endpoint['interface']:
                    continue
                sc[service['type']].append(endpoint)
        return sc

    def get_urls(self, attr=None, filter_value=None,
                 service_type='identity', endpoint_type='public'):
        if endpoint_type:
            endpoint_type = endpoint_type.rstrip('URL')
        sc_endpoints = self.get_endpoints(service_type=service_type,
                                          endpoint_type=endpoint_type)
        endpoints = sc_endpoints.get(service_type)
        if not endpoints:
            return None

        urls = list()
        for endpoint in endpoints:
            if (endpoint['interface'] == endpoint_type
                    and (not self.region_name
                         or endpoint.get('region') == self.region_name)
                    and (not filter_value
                         or endpoint.get(attr) == filter_value)):
                urls.append(endpoint['url'])
        return tuple(urls)

    def url_for(self, attr=None, filter_value=None,
                service_type='identity', endpoint_type='public'):
        catalog = self.get_data()

        if not catalog:
            raise exceptions.EmptyCatalog('The service catalog is empty.')

        if endpoint_type:
            endpoint_type = endpoint_type.rstrip('URL')

        for service in catalog:
            if service['type'] != service_type:
                continue

            endpoints = service['endpoints']
            for endpoint in endpoints:
                if endpoint.get('interface') != endpoint_type:
                    continue
                if (self.region_name and
                        endpoint.get('region') != self.region_name):
                    continue
                if not filter_value or endpoint.get(attr) == filter_value:
                    return endpoint['url']

        raise exceptions.EndpointNotFound('%s endpoint for %s not found.' %
                                          (endpoint_type, service_type))
