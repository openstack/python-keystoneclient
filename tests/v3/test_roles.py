import uuid

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
