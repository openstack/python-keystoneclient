# Copyright 2011 OpenStack LLC.
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

from keystoneclient import base


class Project(base.Resource):
    """Represents an Identity project.

    Attributes:
        * id: a uuid that identifies the project
        * name: project name
        * description: project description
        * enabled: boolean to indicate if project is enabled

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


class ProjectManager(base.CrudManager):
    """Manager class for manipulating Identity projects."""
    resource_class = Project
    collection_key = 'projects'
    key = 'project'

    def create(self, name, domain, description=None, enabled=True, **kwargs):
        return super(ProjectManager, self).create(
            domain_id=base.getid(domain),
            name=name,
            description=description,
            enabled=enabled,
            **kwargs)

    def list(self, domain=None, user=None, **kwargs):
        """List projects.

        If domain or user are provided, then filter projects with
        those attributes.

        If ``**kwargs`` are provided, then filter projects with
        attributes matching ``**kwargs``.
        """
        base_url = '/users/%s' % base.getid(user) if user else None
        return super(ProjectManager, self).list(
            base_url=base_url,
            domain_id=base.getid(domain),
            **kwargs)

    def get(self, project):
        return super(ProjectManager, self).get(
            project_id=base.getid(project))

    def update(self, project, name=None, domain=None, description=None,
               enabled=None, **kwargs):
        return super(ProjectManager, self).update(
            project_id=base.getid(project),
            domain_id=base.getid(domain),
            name=name,
            description=description,
            enabled=enabled,
            **kwargs)

    def delete(self, project):
        return super(ProjectManager, self).delete(
            project_id=base.getid(project))
