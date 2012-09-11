import uuid

from keystoneclient.v3 import projects
from tests.v3 import utils


class ProjectTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(ProjectTests, self).setUp()
        self.additionalSetUp()
        self.key = 'project'
        self.collection_key = 'projects'
        self.model = projects.Project
        self.manager = self.client.projects

    def new_ref(self, **kwargs):
        kwargs = super(ProjectTests, self).new_ref(**kwargs)
        kwargs.setdefault('domain_id', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs
