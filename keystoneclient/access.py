# Copyright 2012 Nebula, Inc.
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


import datetime

from keystoneclient.openstack.common import timeutils


# gap, in seconds, to determine whether the given token is about to expire
STALE_TOKEN_DURATION = 30


class AccessInfo(dict):
    """An object for encapsulating a raw authentication token from keystone
    and helper methods for extracting useful values from that token."""

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def will_expire_soon(self, stale_duration=None):
        """ Determines if expiration is about to occur.

        :return: boolean : true if expiration is within the given duration

        """
        stale_duration = (STALE_TOKEN_DURATION if stale_duration is None
                          else stale_duration)
        norm_expires = timeutils.normalize_time(self.expires)
        # (gyee) should we move auth_token.will_expire_soon() to timeutils
        # instead of duplicating code here?
        soon = (timeutils.utcnow() + datetime.timedelta(
                seconds=stale_duration))
        return norm_expires < soon

    @property
    def expires(self):
        """ Returns the token expiration (as datetime object)

        :returns: datetime

        """
        return timeutils.parse_isotime(self['token']['expires'])

    @property
    def auth_token(self):
        """ Returns the token_id associated with the auth request, to be used
        in headers for authenticating OpenStack API requests.

        :returns: str
        """
        return self['token'].get('id', None)

    @property
    def username(self):
        """ Returns the username associated with the authentication request.
        Follows the pattern defined in the V2 API of first looking for 'name',
        returning that if available, and falling back to 'username' if name
        is unavailable.

        :returns: str
        """
        name = self['user'].get('name', None)
        if name:
            return name
        else:
            return self['user'].get('username', None)

    @property
    def user_id(self):
        """ Returns the user id associated with the authentication request.

        :returns: str
        """
        return self['user'].get('id', None)

    @property
    def tenant_name(self):
        """ Returns the tenant (project) name associated with the
        authentication request.

        :returns: str
        """
        tenant_dict = self['token'].get('tenant', None)
        if tenant_dict:
            return tenant_dict.get('name', None)
        return None

    @property
    def project_name(self):
        """ Synonym for tenant_name """
        return self.tenant_name

    @property
    def scoped(self):
        """ Returns true if the authorization token was scoped to a tenant
        (project), and contains a populated service catalog.

        :returns: bool
        """
        if ('serviceCatalog' in self
            and self['serviceCatalog']
            and 'tenant' in self['token']):
            return True
        return False

    @property
    def tenant_id(self):
        """ Returns the tenant (project) id associated with the authentication
        request, or None if the authentication request wasn't scoped to a
        tenant (project).

        :returns: str
        """
        tenant_dict = self['token'].get('tenant', None)
        if tenant_dict:
            return tenant_dict.get('id', None)
        return None

    @property
    def project_id(self):
        """ Synonym for project_id """
        return self.tenant_id

    @property
    def auth_url(self):
        """ Returns a tuple of URLs from publicURL and adminURL for the service
        'identity' from the service catalog associated with the authorization
        request. If the authentication request wasn't scoped to a tenant
        (project), this property will return None.

        :returns: tuple of urls
        """
        return_list = []
        if 'serviceCatalog' in self and self['serviceCatalog']:
            identity_services = [x for x in self['serviceCatalog']
                                 if x['type'] == 'identity']
            for svc in identity_services:
                for endpoint in svc['endpoints']:
                    if 'publicURL' in endpoint:
                        return_list.append(endpoint['publicURL'])
        if len(return_list) > 0:
            return tuple(return_list)
        return None

    @property
    def management_url(self):
        """ Returns the first adminURL for 'identity' from the service catalog
        associated with the authorization request, or None if the
        authentication request wasn't scoped to a tenant (project).

        :returns: tuple of urls
        """
        return_list = []
        if 'serviceCatalog' in self and self['serviceCatalog']:
            identity_services = [x for x in self['serviceCatalog']
                                 if x['type'] == 'identity']
            for svc in identity_services:
                for endpoint in svc['endpoints']:
                    if 'adminURL' in endpoint:
                        return_list.append(endpoint['adminURL'])
        if len(return_list) > 0:
            return tuple(return_list)
        return None
