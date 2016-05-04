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

from debtcollector import renames
from positional import positional

from keystoneclient import base
from keystoneclient.i18n import _


class Credential(base.Resource):
    """Represents an Identity credential.

    Attributes:
        * id: a uuid that identifies the credential
        * user_id: user ID
        * type: credential type
        * blob: credential data
        * project_id: project ID (optional)

    """

    pass


class CredentialManager(base.CrudManager):
    """Manager class for manipulating Identity credentials."""

    resource_class = Credential
    collection_key = 'credentials'
    key = 'credential'

    def _get_data_blob(self, blob, data):
        # Ref bug #1259461, the <= 0.4.1 keystoneclient calling convention was
        # to pass "data", but the underlying API expects "blob", so
        # support both in the python API for backwards compatibility
        if blob is not None:
            return blob
        elif data is not None:
            return data
        else:
            raise ValueError(
                _("Credential requires blob to be specified"))

    @renames.renamed_kwarg('data', 'blob', version='1.7.0',
                           removal_version='2.0.0')
    @positional(1, enforcement=positional.WARN)
    def create(self, user, type, blob=None, data=None, project=None, **kwargs):
        """Create a credential.

        :param user: User
        :type user: :class:`keystoneclient.v3.users.User` or str
        :param str type: credential type, should be either ``ec2`` or ``cert``
        :param JSON blob: Credential data
        :param JSON data: Deprecated as of the 1.7.0 release in favor of blob
                          and may by removed in the 2.0.0 release.
        :param project: Project, optional
        :type project: :class:`keystoneclient.v3.projects.Project` or str
        :param kwargs: Extra attributes passed to create.

        :raises ValueError: if one of ``blob`` or ``data`` is not specified.

        """
        return super(CredentialManager, self).create(
            user_id=base.getid(user),
            type=type,
            blob=self._get_data_blob(blob, data),
            project_id=base.getid(project),
            **kwargs)

    def get(self, credential):
        """Get a credential.

        :param credential: Credential
        :type credential: :class:`Credential` or str

        """
        return super(CredentialManager, self).get(
            credential_id=base.getid(credential))

    def list(self, **kwargs):
        """List credentials.

        If ``**kwargs`` are provided, then filter credentials with
        attributes matching ``**kwargs``.
        """
        return super(CredentialManager, self).list(**kwargs)

    @renames.renamed_kwarg('data', 'blob', version='1.7.0',
                           removal_version='2.0.0')
    @positional(2, enforcement=positional.WARN)
    def update(self, credential, user, type=None, blob=None, data=None,
               project=None, **kwargs):
        """Update a credential.

        :param credential: Credential to update
        :type credential: :class:`Credential` or str
        :param user: User
        :type user: :class:`keystoneclient.v3.users.User` or str
        :param str type: credential type, should be either ``ec2`` or ``cert``
        :param JSON blob: Credential data
        :param JSON data: Deprecated as of the 1.7.0 release in favor of blob
                          and may be removed in the 2.0.0 release.
        :param project: Project
        :type project: :class:`keystoneclient.v3.projects.Project` or str
        :param kwargs: Extra attributes passed to create.

        :raises ValueError: if one of ``blob`` or ``data`` is not specified.

        """
        return super(CredentialManager, self).update(
            credential_id=base.getid(credential),
            user_id=base.getid(user),
            type=type,
            blob=self._get_data_blob(blob, data),
            project_id=base.getid(project),
            **kwargs)

    def delete(self, credential):
        """Delete a credential.

        :param credential: Credential
        :type credential: :class:`Credential` or str

        """
        return super(CredentialManager, self).delete(
            credential_id=base.getid(credential))
