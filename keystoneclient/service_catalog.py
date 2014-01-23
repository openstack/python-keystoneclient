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

import abc

import six

from keystoneclient import exceptions


@six.add_metaclass(abc.ABCMeta)
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

    def __init__(self, region_name=None):
        self._region_name = region_name

    @property
    def region_name(self):
        # FIXME(jamielennox): Having region_name set on the service catalog
        # directly is deprecated. It should instead be provided as a parameter
        # to calls made to the service_catalog. Provide appropriate warning.
        return self._region_name

    @abc.abstractmethod
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

    @abc.abstractmethod
    def _is_endpoint_type_match(self, endpoint, endpoint_type):
        """Helper function to normalize endpoint matching across v2 and v3.

        :returns: True if the provided endpoint matches the required
        endpoint_type otherwise False.
        """

    @abc.abstractmethod
    def _normalize_endpoint_type(self, endpoint_type):
        """Handle differences in the way v2 and v3 catalogs specify endpoint.

        Both v2 and v3 must be able to handle the endpoint style of the other.
        For example v2 must be able to handle a 'public' endpoint_type and
        v3 must be able to handle a 'publicURL' endpoint_type.

        :returns: the endpoint string in the format appropriate for this
                  service catalog.
        """

    def get_endpoints(self, service_type=None, endpoint_type=None,
                      region_name=None):
        """Fetch and filter endpoints for the specified service(s).

        Returns endpoints for the specified service (or all) containing
        the specified type (or all) and region (or all).
        """
        endpoint_type = self._normalize_endpoint_type(endpoint_type)
        region_name = region_name or self._region_name

        sc = {}

        for service in (self.get_data() or []):
            try:
                st = service['type']
            except KeyError:
                continue

            if service_type and service_type != st:
                continue

            sc[st] = []

            for endpoint in service.get('endpoints', []):
                if (endpoint_type and not
                        self._is_endpoint_type_match(endpoint, endpoint_type)):
                    continue
                if region_name and region_name != endpoint.get('region'):
                    continue
                sc[st].append(endpoint)

        return sc

    def _get_service_endpoints(self, attr, filter_value, service_type,
                               endpoint_type, region_name):
        """Fetch the endpoints of a particular service_type and handle
        the filtering.
        """
        sc_endpoints = self.get_endpoints(service_type=service_type,
                                          endpoint_type=endpoint_type,
                                          region_name=region_name)

        try:
            endpoints = sc_endpoints[service_type]
        except KeyError:
            return

        # TODO(jamielennox): at least swiftclient is known to set attr and not
        # filter_value and expects that to mean that filtering is ignored, so
        # we can't check for the presence of attr. This behaviour should be
        # deprecated and an appropriate warning provided.
        if filter_value:
            return [endpoint for endpoint in endpoints
                    if endpoint.get(attr) == filter_value]

        return endpoints

    @abc.abstractmethod
    def get_urls(self, attr=None, filter_value=None,
                 service_type='identity', endpoint_type='publicURL',
                 region_name=None):
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
                service_type='identity', endpoint_type='publicURL',
                region_name=None):
        """Fetch an endpoint from the service catalog.

        Fetch the specified endpoint from the service catalog for
        a particular endpoint attribute. If no attribute is given, return
        the first endpoint of the specified type.

        Valid endpoint types: `public` or `publicURL`,
                              `internal` or `internalURL`,
                              `admin` or 'adminURL`
        """
        if not self.get_data():
            raise exceptions.EmptyCatalog('The service catalog is empty.')

        urls = self.get_urls(attr=attr,
                             filter_value=filter_value,
                             service_type=service_type,
                             endpoint_type=endpoint_type,
                             region_name=region_name)

        try:
            return urls[0]
        except Exception:
            pass

        msg = '%(endpoint)s endpoint for %(service)s%(region)s not found'
        region = ' in %s region' % region_name if region_name else ''
        msg = msg % {'endpoint': endpoint_type,
                     'service': service_type,
                     'region': region}

        raise exceptions.EndpointNotFound(msg)

    @abc.abstractmethod
    def get_data(self):
        """Get the raw catalog structure.

        Get the version dependent catalog structure as it is presented within
        the resource.

        :returns: list containing raw catalog data entries or None
        """
        raise NotImplementedError()


class ServiceCatalogV2(ServiceCatalog):
    """An object for encapsulating the service catalog using raw v2 auth token
    from Keystone.
    """

    def __init__(self, resource_dict, region_name=None):
        self.catalog = resource_dict
        super(ServiceCatalogV2, self).__init__(region_name=region_name)

    @classmethod
    def is_valid(cls, resource_dict):
        # This class is also used for reading token info of an unscoped token.
        # Unscoped token does not have 'serviceCatalog' in V2, checking this
        # will not work. Use 'token' attribute instead.
        return 'token' in resource_dict

    def _normalize_endpoint_type(self, endpoint_type):
        if endpoint_type and 'URL' not in endpoint_type:
            endpoint_type = endpoint_type + 'URL'

        return endpoint_type

    def _is_endpoint_type_match(self, endpoint, endpoint_type):
        return endpoint_type in endpoint

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

    def get_urls(self, attr=None, filter_value=None,
                 service_type='identity', endpoint_type='publicURL',
                 region_name=None):
        endpoint_type = self._normalize_endpoint_type(endpoint_type)
        endpoints = self._get_service_endpoints(attr=attr,
                                                filter_value=filter_value,
                                                service_type=service_type,
                                                endpoint_type=endpoint_type,
                                                region_name=region_name)

        if endpoints:
            return tuple([endpoint[endpoint_type] for endpoint in endpoints])
        else:
            return None


class ServiceCatalogV3(ServiceCatalog):
    """An object for encapsulating the service catalog using raw v3 auth token
    from Keystone.
    """

    def __init__(self, token, resource_dict, region_name=None):
        super(ServiceCatalogV3, self).__init__(region_name=region_name)
        self._auth_token = token
        self.catalog = resource_dict

    @classmethod
    def is_valid(cls, resource_dict):
        # This class is also used for reading token info of an unscoped token.
        # Unscoped token does not have 'catalog', checking this
        # will not work. Use 'methods' attribute instead.
        return 'methods' in resource_dict

    def _normalize_endpoint_type(self, endpoint_type):
        if endpoint_type:
            endpoint_type = endpoint_type.rstrip('URL')

        return endpoint_type

    def _is_endpoint_type_match(self, endpoint, endpoint_type):
        try:
            return endpoint_type == endpoint['interface']
        except KeyError:
            return False

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

    def get_urls(self, attr=None, filter_value=None,
                 service_type='identity', endpoint_type='public',
                 region_name=None):
        endpoints = self._get_service_endpoints(attr=attr,
                                                filter_value=filter_value,
                                                service_type=service_type,
                                                endpoint_type=endpoint_type,
                                                region_name=region_name)

        if endpoints:
            return tuple([endpoint['url'] for endpoint in endpoints])
        else:
            return None
