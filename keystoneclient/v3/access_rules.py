# Copyright 2019 SUSE LLC
#
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

from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient.i18n import _


class AccessRule(base.Resource):
    """Represents an Identity access rule for application credentials.

    Attributes:
        * id: a uuid that identifies the access rule
        * method: The request method that the application credential is
             permitted to use for a given API endpoint
        * path: The API path that the application credential is permitted to
            access
        * service: The service type identifier for the service that the
             application credential is permitted to access

    """

    pass


class AccessRuleManager(base.CrudManager):
    """Manager class for manipulating Identity access rules."""

    resource_class = AccessRule
    collection_key = 'access_rules'
    key = 'access_rule'

    def get(self, access_rule, user=None):
        """Retrieve an access rule.

        :param access_rule: the access rule to be retrieved from the
            server
        :type access_rule: str or
            :class:`keystoneclient.v3.access_rules.AccessRule`
        :param string user: User ID

        :returns: the specified access rule
        :rtype:
            :class:`keystoneclient.v3.access_rules.AccessRule`

        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        return super(AccessRuleManager, self).get(
            access_rule_id=base.getid(access_rule))

    def list(self, user=None, **kwargs):
        """List access rules.

        :param string user: User ID

        :returns: a list of access rules
        :rtype: list of
            :class:`keystoneclient.v3.access_rules.AccessRule`
        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        return super(AccessRuleManager, self).list(**kwargs)

    def find(self, user=None, **kwargs):
        """Find an access rule with attributes matching ``**kwargs``.

        :param string user: User ID

        :returns: a list of matching access rules
        :rtype: list of
            :class:`keystoneclient.v3.access_rules.AccessRule`
        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        return super(AccessRuleManager, self).find(**kwargs)

    def delete(self, access_rule, user=None):
        """Delete an access rule.

        :param access_rule: the access rule to be deleted
        :type access_rule: str or
            :class:`keystoneclient.v3.access_rules.AccessRule`
        :param string user: User ID

        :returns: response object with 204 status
        :rtype: :class:`requests.models.Response`

        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        return super(AccessRuleManager, self).delete(
            access_rule_id=base.getid(access_rule))

    def update(self):
        raise exceptions.MethodNotImplemented(
            _('Access rules are immutable, updating is not'
              ' supported.'))

    def create(self):
        raise exceptions.MethodNotImplemented(
            _('Access rules can only be created as attributes of application '
              'credentials.'))
