# Copyright 2011 OpenStack Foundation
# Copyright 2011 Nebula, Inc.
# All Rights Reserved.
#
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

from positional import positional

from keystoneclient import base


class Credential(base.Resource):
    """Represents an Identity credential.

    Attributes:
        * id: a uuid that identifies the credential
        * user_id: user ID to which credential belongs
        * type: the type of credential
        * blob: the text that represents the credential
        * project_id: project ID which limits the scope of the credential

    """

    pass


class CredentialManager(base.CrudManager):
    """Manager class for manipulating Identity credentials."""

    resource_class = Credential
    collection_key = 'credentials'
    key = 'credential'

    @positional(1, enforcement=positional.WARN)
    def create(self, user, type, blob, project=None, **kwargs):
        """Create a credential.

        :param user: the user to which the credential belongs
        :type user: str or :class:`keystoneclient.v3.users.User`
        :param str type: the type of the credential, valid values are:
                         ``ec2``, ``cert`` or ``totp``
        :param str blob: the arbitrary blob of the credential data, to be
                         parsed according to the type
        :param project: the project which limits the scope of the credential,
                        this attribbute is mandatory if the credential type is
                        ec2
        :type project: str or :class:`keystoneclient.v3.projects.Project`
        :param kwargs: any other attribute provided will be passed to the
                       server

        :returns: the created credential
        :rtype: :class:`keystoneclient.v3.credentials.Credential`

        """
        return super(CredentialManager, self).create(
            user_id=base.getid(user),
            type=type,
            blob=blob,
            project_id=base.getid(project),
            **kwargs)

    def get(self, credential):
        """Retrieve a credential.

        :param credential: the credential to be retrieved from the server
        :type credential: str or
                          :class:`keystoneclient.v3.credentials.Credential`

        :returns: the specified credential
        :rtype: :class:`keystoneclient.v3.credentials.Credential`

        """
        return super(CredentialManager, self).get(
            credential_id=base.getid(credential))

    def list(self, **kwargs):
        """List credentials.

        :param kwargs: If user_id or type is specified then credentials
                       will be filtered accordingly.

        :returns: a list of credentials
        :rtype: list of :class:`keystoneclient.v3.credentials.Credential`

        """
        return super(CredentialManager, self).list(**kwargs)

    @positional(2, enforcement=positional.WARN)
    def update(self, credential, user, type=None, blob=None, project=None,
               **kwargs):
        """Update a credential.

        :param credential: the credential to be updated on the server
        :type credential: str or
                         :class:`keystoneclient.v3.credentials.Credential`
        :param user: the new user to which the credential belongs
        :type user: str or :class:`keystoneclient.v3.users.User`
        :param str type: the new type of the credential, valid values are:
                         ``ec2``, ``cert`` or ``totp``
        :param str blob: the new blob of the credential data
                          and may be removed in the future release.
        :param project: the new project which limits the scope of the
                        credential, this attribute is mandatory if the
                        credential type is ec2
        :type project: str or :class:`keystoneclient.v3.projects.Project`
        :param kwargs: any other attribute provided will be passed to the
                       server

        :returns: the updated credential
        :rtype: :class:`keystoneclient.v3.credentials.Credential`

        """
        return super(CredentialManager, self).update(
            credential_id=base.getid(credential),
            user_id=base.getid(user),
            type=type,
            blob=blob,
            project_id=base.getid(project),
            **kwargs)

    def delete(self, credential):
        """Delete a credential.

        :param credential: the credential to be deleted
        :type credential: str or
                          :class:`keystoneclient.v3.credentials.Credential`

        :returns: response object with 204 status
        :rtype: :class:`requests.models.Response`

        """
        return super(CredentialManager, self).delete(
            credential_id=base.getid(credential))
