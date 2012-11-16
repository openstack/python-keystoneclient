import copy
import urlparse
import uuid

import requests

from keystoneclient import exceptions
from keystoneclient.v3 import roles
from tests.v3 import utils


class RoleTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(RoleTests, self).setUp()
        self.additionalSetUp()
        self.key = 'role'
        self.collection_key = 'roles'
        self.model = roles.Role
        self.manager = self.client.roles

    def new_ref(self, **kwargs):
        kwargs = super(RoleTests, self).new_ref(**kwargs)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs

    def test_domain_role_grant(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 201,
            "text": '',
        })

        method = 'PUT'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/domains/%s/users/%s/%s/%s' % (
                    domain_id, user_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.grant(role=ref['id'], domain=domain_id, user=user_id)

    def test_domain_role_list(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]
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
                'v3/domains/%s/users/%s/%s' % (
                    domain_id, user_id, self.collection_key)),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.list(domain=domain_id, user=user_id)

    def test_domain_role_check(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 200,
            "text": '',
        })

        method = 'HEAD'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/domains/%s/users/%s/%s/%s' % (
                    domain_id, user_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.check(role=ref['id'], domain=domain_id, user=user_id)

    def test_domain_role_revoke(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 204,
            "text": '',
        })

        method = 'DELETE'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/domains/%s/users/%s/%s/%s' % (
                    domain_id, user_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.revoke(role=ref['id'], domain=domain_id, user=user_id)

    def test_project_role_grant(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 201,
            "text": '',
        })

        method = 'PUT'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/projects/%s/users/%s/%s/%s' % (
                    project_id, user_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.grant(role=ref['id'], project=project_id, user=user_id)

    def test_project_role_list(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]
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
                'v3/projects/%s/users/%s/%s' % (
                    project_id, user_id, self.collection_key)),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.list(project=project_id, user=user_id)

    def test_project_role_check(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 200,
            "text": '',
        })

        method = 'HEAD'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/projects/%s/users/%s/%s/%s' % (
                    project_id, user_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.check(role=ref['id'], project=project_id, user=user_id)

    def test_project_role_revoke(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = utils.TestResponse({
            "status_code": 204,
            "text": '',
        })

        method = 'DELETE'
        kwargs = copy.copy(self.TEST_REQUEST_BASE)
        kwargs['headers'] = self.headers[method]
        requests.request(
            method,
            urlparse.urljoin(
                self.TEST_URL,
                'v3/projects/%s/users/%s/%s/%s' % (
                    project_id, user_id, self.collection_key, ref['id'])),
            **kwargs).AndReturn((resp))
        self.mox.ReplayAll()

        self.manager.revoke(role=ref['id'], project=project_id, user=user_id)

    def test_domain_project_role_grant_fails(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.grant,
            role=ref['id'],
            domain=domain_id,
            project=project_id,
            user=user_id)

    def test_domain_project_role_list_fails(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.list,
            domain=domain_id,
            project=project_id,
            user=user_id)

    def test_domain_project_role_check_fails(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.check,
            role=ref['id'],
            domain=domain_id,
            project=project_id,
            user=user_id)

    def test_domain_project_role_revoke_fails(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()

        self.assertRaises(
            exceptions.ValidationError,
            self.manager.revoke,
            role=ref['id'],
            domain=domain_id,
            project=project_id,
            user=user_id)
