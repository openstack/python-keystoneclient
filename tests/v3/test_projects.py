import copy
import urlparse
import uuid

import requests

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

    def test_list_projects_for_user(self):
        ref_list = [self.new_ref(), self.new_ref()]

        user_id = uuid.uuid4().hex
        resp = utils.TestResponse({
            "status-code": 200,
            "text": self.serialize(ref_list),
        })

        method = 'GET'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/users/%s/%s' % (user_id, self.collection_key)),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned_list = self.manager.list(user=user_id)
        self.assertTrue(len(returned_list))
        [self.assertTrue(isinstance(r, self.model)) for r in returned_list]

    def test_list_projects_for_domain(self):
        ref_list = [self.new_ref(), self.new_ref()]

        domain_id = uuid.uuid4().hex
        resp = utils.TestResponse({
            "status_code": 200,
            "text": self.serialize(ref_list),
        })

        method = 'GET'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/%s?domain_id=%s' % (self.collection_key, domain_id)),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        returned_list = self.manager.list(domain=domain_id)
        self.assertTrue(len(returned_list))
        [self.assertTrue(isinstance(r, self.model)) for r in returned_list]
