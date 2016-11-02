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

from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient.i18n import _


class DomainConfig(base.Resource):
    """An object representing a domain config association.

    This resource object does not necessarily contain fixed attributes, as new
    attributes are added in the server, they are supported here directly.
    The currently supported configs are `identity` and `ldap`.

    """

    pass


class DomainConfigManager(base.Manager):
    """Manager class for manipulating domain config associations."""

    resource_class = DomainConfig
    key = 'config'

    def build_url(self, domain):
        return '/domains/%s/config' % base.getid(domain)

    def create(self, domain, config):
        """Create a config for a domain.

        :param domain: the domain where the config is going to be applied.
        :type domain: str or :py:class:`keystoneclient.v3.domains.Domain`

        :param dict config: a dictionary of domain configurations.

        Example of the ``config`` parameter::

            {
                 "identity": {
                     "driver": "ldap"
                 },
                 "ldap": {
                     "url": "ldap://myldap.com:389/",
                     "user_tree_dn": "ou=Users,dc=my_new_root,dc=org"
                 }
            }

        :returns: the created domain config returned from server.
        :rtype: :class:`keystoneclient.v3.domain_configs.DomainConfig`

        """
        base_url = self.build_url(domain)
        body = {self.key: config}
        return super(DomainConfigManager, self)._put(
            base_url, body=body, response_key=self.key)

    def get(self, domain):
        """Get a config for a domain.

        :param domain: the domain for which the config is defined.
        :type domain: str or :py:class:`keystoneclient.v3.domains.Domain`

        :returns: the domain config returned from server.
        :rtype: :class:`keystoneclient.v3.domain_configs.DomainConfig`

        """
        base_url = self.build_url(domain)
        return super(DomainConfigManager, self)._get(base_url, self.key)

    def update(self, domain, config):
        """Update a config for a domain.

        :param domain: the domain where the config is going to be updated.
        :type domain: str or :py:class:`keystoneclient.v3.domains.Domain`

        :param dict config: a dictionary of domain configurations.

        Example of the ``config`` parameter::

            {
                 "identity": {
                     "driver": "ldap"
                 },
                 "ldap": {
                     "url": "ldap://myldap.com:389/",
                     "user_tree_dn": "ou=Users,dc=my_new_root,dc=org"
                 }
            }

        :returns: the updated domain config returned from server.
        :rtype: :class:`keystoneclient.v3.domain_configs.DomainConfig`

        """
        base_url = self.build_url(domain)
        body = {self.key: config}
        return super(DomainConfigManager, self)._patch(
            base_url, body=body, response_key=self.key)

    def delete(self, domain):
        """Delete a config for a domain.

        :param domain: the domain which the config will be deleted on
                       the server.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        base_url = self.build_url(domain)
        return super(DomainConfigManager, self)._delete(url=base_url)

    def find(self, **kwargs):
        raise exceptions.MethodNotImplemented(
            _('Find not supported for domain configs'))

    def list(self, **kwargs):
        raise exceptions.MethodNotImplemented(
            _('List not supported for domain configs'))
