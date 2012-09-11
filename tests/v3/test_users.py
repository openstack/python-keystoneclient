import uuid

from keystoneclient.v3 import users
from tests.v3 import utils


class UserTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(UserTests, self).setUp()
        self.additionalSetUp()
        self.key = 'user'
        self.collection_key = 'users'
        self.model = users.User
        self.manager = self.client.users

    def new_ref(self, **kwargs):
        kwargs = super(UserTests, self).new_ref(**kwargs)
        kwargs.setdefault('description', uuid.uuid4().hex)
        kwargs.setdefault('domain_id', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('project_id', uuid.uuid4().hex)
        return kwargs
