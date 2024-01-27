# Copyright 2018 SUSE Linux GmbH
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
from keystoneclient import utils


class ApplicationCredential(base.Resource):
    """Represents an Identity application credential.

    Attributes:
        * id: a uuid that identifies the application credential
        * user: the user who owns the application credential
        * name: application credential name
        * secret: application credential secret
        * description: application credential description
        * expires_at: expiry time
        * roles: role assignments on the project
        * unrestricted: whether the application credential has restrictions
            applied
        * access_rules: a list of access rules defining what API requests the
            application credential may be used for

    """

    pass


class ApplicationCredentialManager(base.CrudManager):
    """Manager class for manipulating Identity application credentials."""

    resource_class = ApplicationCredential
    collection_key = 'application_credentials'
    key = 'application_credential'

    def create(self, name, user=None, secret=None, description=None,
               expires_at=None, roles=None,
               unrestricted=False, access_rules=None, **kwargs):
        """Create a credential.

        :param string name: application credential name
        :param string user: User ID
        :param secret: application credential secret
        :param description: application credential description
        :param datetime.datetime expires_at: expiry time
        :param List roles: list of roles on the project. Maybe a list of IDs
            or a list of dicts specifying role name and domain
        :param bool unrestricted: whether the application credential has
            restrictions applied
        :param List access_rules: a list of dicts representing access rules

        :returns: the created application credential
        :rtype:
            :class:`keystoneclient.v3.application_credentials.ApplicationCredential`

        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        # Convert roles list into list-of-dict API format
        role_list = []
        if roles:
            if not isinstance(roles, list):
                roles = [roles]
            for role in roles:
                if isinstance(role, str):
                    role_list.extend([{'id': role}])
                elif isinstance(role, dict):
                    role_list.extend([role])
                else:
                    msg = (_("Roles must be a list of IDs or role dicts."))
                    raise exceptions.CommandError(msg)

        if not role_list:
            role_list = None

        # Convert datetime.datetime expires_at to iso format string
        if expires_at:
            expires_str = utils.isotime(at=expires_at, subsecond=True)
        else:
            expires_str = None

        return super(ApplicationCredentialManager, self).create(
            name=name,
            secret=secret,
            description=description,
            expires_at=expires_str,
            roles=role_list,
            unrestricted=unrestricted,
            access_rules=access_rules,
            **kwargs)

    def get(self, application_credential, user=None):
        """Retrieve an application credential.

        :param application_credential: the credential to be retrieved from the
            server
        :type applicationcredential: str or
            :class:`keystoneclient.v3.application_credentials.ApplicationCredential`

        :returns: the specified application credential
        :rtype:
            :class:`keystoneclient.v3.application_credentials.ApplicationCredential`

        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        return super(ApplicationCredentialManager, self).get(
            application_credential_id=base.getid(application_credential))

    def list(self, user=None, **kwargs):
        """List application credentials.

        :param string user: User ID

        :returns: a list of application credentials
        :rtype: list of
            :class:`keystoneclient.v3.application_credentials.ApplicationCredential`
        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        return super(ApplicationCredentialManager, self).list(**kwargs)

    def find(self, user=None, **kwargs):
        """Find an application credential with attributes matching ``**kwargs``.  # noqa

        :param string user: User ID

        :returns: a list of matching application credentials
        :rtype: list of
            :class:`keystoneclient.v3.application_credentials.ApplicationCredential`
        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        return super(ApplicationCredentialManager, self).find(**kwargs)

    def delete(self, application_credential, user=None):
        """Delete an application credential.

        :param application_credential: the application credential to be deleted
        :type credential: str or
            :class:`keystoneclient.v3.application_credentials.ApplicationCredential`

        :returns: response object with 204 status
        :rtype: :class:`requests.models.Response`

        """
        user = user or self.client.user_id
        self.base_url = '/users/%(user)s' % {'user': user}

        return super(ApplicationCredentialManager, self).delete(
            application_credential_id=base.getid(application_credential))

    def update(self):
        raise exceptions.MethodNotImplemented(
            _('Application credentials are immutable, updating is not'
              ' supported.'))
