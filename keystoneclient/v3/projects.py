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

import six.moves.urllib as urllib

from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient.i18n import _


class Project(base.Resource):
    """Represents an Identity project.

    Attributes:
        * id: a uuid that identifies the project
        * name: project name
        * description: project description
        * enabled: boolean to indicate if project is enabled
        * parent_id: a uuid representing this project's parent in hierarchy
        * parents: a list or a structured dict containing the parents of this
                   project in the hierarchy
        * subtree: a list or a structured dict containing the subtree of this
                   project in the hierarchy

    """

    def update(self, name=None, description=None, enabled=None):
        kwargs = {
            'name': name if name is not None else self.name,
            'description': (description
                            if description is not None
                            else self.description),
            'enabled': enabled if enabled is not None else self.enabled,
        }

        try:
            retval = self.manager.update(self.id, **kwargs)
            self = retval
        except Exception:
            retval = None

        return retval

    def add_tag(self, tag):
        self.manager.add_tag(self, tag)

    def update_tags(self, tags):
        return self.manager.update_tags(self, tags)

    def delete_tag(self, tag):
        self.manager.delete_tag(self, tag)

    def delete_all_tags(self):
        return self.manager.update_tags(self, [])

    def list_tags(self):
        return self.manager.list_tags(self)

    def check_tag(self, tag):
        return self.manager.check_tag(self, tag)


class ProjectManager(base.CrudManager):
    """Manager class for manipulating Identity projects."""

    resource_class = Project
    collection_key = 'projects'
    key = 'project'

    def create(self, name, domain, description=None,
               enabled=True, parent=None, **kwargs):
        """Create a project.

        :param str name: the name of the project.
        :param domain: the domain of the project.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`
        :param str description: the description of the project.
        :param bool enabled: whether the project is enabled.
        :param parent: the parent of the project in the hierarchy.
        :type parent: str or :class:`keystoneclient.v3.projects.Project`
        :param kwargs: any other attribute provided will be passed to the
                       server.

        :returns: the created project returned from server.
        :rtype: :class:`keystoneclient.v3.projects.Project`

        """
        # NOTE(rodrigods): the API must be backwards compatible, so if an
        # application was passing a 'parent_id' before as kwargs, the call
        # should not fail. If both 'parent' and 'parent_id' are provided,
        # 'parent' will be preferred.
        if parent:
            kwargs['parent_id'] = base.getid(parent)

        return super(ProjectManager, self).create(
            domain_id=base.getid(domain),
            name=name,
            description=description,
            enabled=enabled,
            **kwargs)

    def list(self, domain=None, user=None, parent=None, **kwargs):
        """List projects.

        :param domain: the domain of the projects to be filtered on.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`
        :param user: filter in projects the specified user has role
                     assignments on.
        :type user: str or :class:`keystoneclient.v3.users.User`
        :param parent: filter in projects the specified project is a parent
                       for
        :type parent: str or :class:`keystoneclient.v3.projects.Project`
        :param kwargs: any other attribute provided will filter projects on.
                       Project tags filter keyword: ``tags``, ``tags_any``,
                       ``not_tags``, and ``not_tags_any``. tag attribute type
                       string. Pass in a comma separated string to filter
                       with multiple tags.

        :returns: a list of projects.
        :rtype: list of :class:`keystoneclient.v3.projects.Project`

        """
        base_url = '/users/%s' % base.getid(user) if user else None
        projects = super(ProjectManager, self).list(
            base_url=base_url,
            domain_id=base.getid(domain),
            parent_id=base.getid(parent),
            fallback_to_auth=True,
            **kwargs)

        base_response = None
        list_data = projects
        if self.client.include_metadata:
            base_response = projects
            list_data = projects.data
            base_response.data = list_data

        for p in list_data:
            p.tags = self._encode_tags(getattr(p, 'tags', []))

        if self.client.include_metadata:
            base_response.data = list_data

        return base_response if self.client.include_metadata else list_data

    def _check_not_parents_as_ids_and_parents_as_list(self, parents_as_ids,
                                                      parents_as_list):
        if parents_as_ids and parents_as_list:
            msg = _('Specify either parents_as_ids or parents_as_list '
                    'parameters, not both')
            raise exceptions.ValidationError(msg)

    def _check_not_subtree_as_ids_and_subtree_as_list(self, subtree_as_ids,
                                                      subtree_as_list):
        if subtree_as_ids and subtree_as_list:
            msg = _('Specify either subtree_as_ids or subtree_as_list '
                    'parameters, not both')
            raise exceptions.ValidationError(msg)

    def get(self, project, subtree_as_list=False, parents_as_list=False,
            subtree_as_ids=False, parents_as_ids=False):
        """Retrieve a project.

        :param project: the project to be retrieved from the server.
        :type project: str or :class:`keystoneclient.v3.projects.Project`
        :param bool subtree_as_list: retrieve projects below this project in
                                     the hierarchy as a flat list. It only
                                     includes the projects in which the current
                                     user has role assignments on.
        :param bool parents_as_list: retrieve projects above this project in
                                     the hierarchy as a flat list. It only
                                     includes the projects in which the current
                                     user has role assignments on.
        :param bool subtree_as_ids: retrieve the IDs from the projects below
                                    this project in the hierarchy as a
                                    structured dictionary.
        :param bool parents_as_ids: retrieve the IDs from the projects above
                                    this project in the hierarchy as a
                                    structured dictionary.
        :returns: the specified project returned from server.
        :rtype: :class:`keystoneclient.v3.projects.Project`

        :raises keystoneclient.exceptions.ValidationError: if subtree_as_list
            and subtree_as_ids or parents_as_list and parents_as_ids are
            included at the same time in the call.

        """
        self._check_not_parents_as_ids_and_parents_as_list(
            parents_as_ids, parents_as_list)
        self._check_not_subtree_as_ids_and_subtree_as_list(
            subtree_as_ids, subtree_as_list)

        # According to the API spec, the query params are key only
        query_params = []
        if subtree_as_list:
            query_params.append('subtree_as_list')
        if subtree_as_ids:
            query_params.append('subtree_as_ids')
        if parents_as_list:
            query_params.append('parents_as_list')
        if parents_as_ids:
            query_params.append('parents_as_ids')

        query = self.build_key_only_query(query_params)
        dict_args = {'project_id': base.getid(project)}
        url = self.build_url(dict_args_in_out=dict_args)
        p = self._get(url + query, self.key)
        p.tags = self._encode_tags(getattr(p, 'tags', []))
        return p

    def find(self, **kwargs):
        p = super(ProjectManager, self).find(**kwargs)
        p.tags = self._encode_tags(getattr(p, 'tags', []))
        return p

    def update(self, project, name=None, domain=None, description=None,
               enabled=None, **kwargs):
        """Update a project.

        :param project: the project to be updated on the server.
        :type project: str or :class:`keystoneclient.v3.projects.Project`
        :param str name: the new name of the project.
        :param domain: the new domain of the project.
        :type domain: str or :class:`keystoneclient.v3.domains.Domain`
        :param str description: the new description of the project.
        :param bool enabled: whether the project is enabled.
        :param kwargs: any other attribute provided will be passed to server.

        :returns: the updated project returned from server.
        :rtype: :class:`keystoneclient.v3.projects.Project`

        """
        return super(ProjectManager, self).update(
            project_id=base.getid(project),
            domain_id=base.getid(domain),
            name=name,
            description=description,
            enabled=enabled,
            **kwargs)

    def delete(self, project):
        """Delete a project.

        :param project: the project to be deleted on the server.
        :type project: str or :class:`keystoneclient.v3.projects.Project`

        :returns: Response object with 204 status.
        :rtype: :class:`requests.models.Response`

        """
        return super(ProjectManager, self).delete(
            project_id=base.getid(project))

    def _encode_tags(self, tags):
        """Encode tags to non-unicode string in python2.

        :param tags: list of unicode tags

        :returns: List of strings
        """
        return [str(t) for t in tags]

    def add_tag(self, project, tag):
        """Add a tag to a project.

        :param project: project to add a tag to.
        :param tag: str name of tag.

        """
        url = "/projects/%s/tags/%s" % (base.getid(project),
                                        urllib.parse.quote(tag))
        return self._put(url)

    def update_tags(self, project, tags):
        """Update tag list of a project.

        Replaces current tag list with list specified in tags parameter.

        :param project: project to update.
        :param tags: list of str tag names to add to the project

        :returns: list of tags

        """
        url = "/projects/%s/tags" % base.getid(project)
        for tag in tags:
            tag = urllib.parse.quote(tag)
        resp, body = self.client.put(url, body={"tags": tags})
        return self._prepare_return_value(resp, body['tags'])

    def delete_tag(self, project, tag):
        """Remove tag from project.

        :param projectd: project to remove tag from.
        :param tag: str name of tag to remove from project

        """
        return self._delete(
            "/projects/%s/tags/%s" % (base.getid(project),
                                      urllib.parse.quote(tag)))

    def list_tags(self, project):
        """List tags associated with project.

        :param project: project to list tags for.

        :returns: list of str tag names

        """
        url = "/projects/%s/tags" % base.getid(project)
        resp, body = self.client.get(url)
        body['tags'] = self._encode_tags(body['tags'])
        return self._prepare_return_value(resp, body['tags'])

    def check_tag(self, project, tag):
        """Check if tag is associated with project.

        :param project: project to check tags for.
        :param tag: str name of tag

        :returns: true if tag is associated, false otherwise

        """
        url = "/projects/%s/tags/%s" % (base.getid(project),
                                        urllib.parse.quote(tag))
        try:
            resp, body = self.client.head(url)
            # no errors means found the tag
            return self._prepare_return_value(resp, True)
        except exceptions.HttpError as ex:
            # return false with request_id if include_metadata=True
            return self._prepare_return_value(ex.response, False)
