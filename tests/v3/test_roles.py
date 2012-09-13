import httplib2
import urlparse
import uuid

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
        resp = httplib2.Response({
            'status': 201,
            'body': '',
        })

        method = 'PUT'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/domains/%s/users/%s/%s/%s' % (
                    domain_id, user_id, self.collection_key, ref['id'])),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.manager.grant(role=ref['id'], domain=domain_id, user=user_id)

    def test_domain_role_list(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]
        resp = httplib2.Response({
            'status': 200,
            'body': self.serialize(ref_list),
        })

        method = 'GET'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/domains/%s/users/%s/%s' % (
                    domain_id, user_id, self.collection_key)),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.manager.list(domain=domain_id, user=user_id)

    def test_domain_role_check(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = httplib2.Response({
            'status': 200,
            'body': '',
        })

        method = 'HEAD'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/domains/%s/users/%s/%s/%s' % (
                    domain_id, user_id, self.collection_key, ref['id'])),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.manager.check(role=ref['id'], domain=domain_id, user=user_id)

    def test_domain_role_revoke(self):
        user_id = uuid.uuid4().hex
        domain_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = httplib2.Response({
            'status': 204,
            'body': '',
        })

        method = 'DELETE'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/domains/%s/users/%s/%s/%s' % (
                    domain_id, user_id, self.collection_key, ref['id'])),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.manager.revoke(role=ref['id'], domain=domain_id, user=user_id)

    def test_project_role_grant(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = httplib2.Response({
            'status': 201,
            'body': '',
        })

        method = 'PUT'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/projects/%s/users/%s/%s/%s' % (
                    project_id, user_id, self.collection_key, ref['id'])),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.manager.grant(role=ref['id'], project=project_id, user=user_id)

    def test_project_role_list(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref_list = [self.new_ref(), self.new_ref()]
        resp = httplib2.Response({
            'status': 200,
            'body': self.serialize(ref_list),
        })

        method = 'GET'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/projects/%s/users/%s/%s' % (
                    project_id, user_id, self.collection_key)),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.manager.list(project=project_id, user=user_id)

    def test_project_role_check(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = httplib2.Response({
            'status': 200,
            'body': '',
        })

        method = 'HEAD'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/projects/%s/users/%s/%s/%s' % (
                    project_id, user_id, self.collection_key, ref['id'])),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
        self.mox.ReplayAll()

        self.manager.check(role=ref['id'], project=project_id, user=user_id)

    def test_project_role_revoke(self):
        user_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex
        ref = self.new_ref()
        resp = httplib2.Response({
            'status': 204,
            'body': '',
        })

        method = 'DELETE'
        httplib2.Http.request(
            urlparse.urljoin(
                self.TEST_URL,
                'v3/projects/%s/users/%s/%s/%s' % (
                    project_id, user_id, self.collection_key, ref['id'])),
            method,
            headers=self.headers[method]) \
            .AndReturn((resp, resp['body']))
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
