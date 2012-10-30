import uuid

from keystoneclient.v3 import policies
from tests.v3 import utils


class PolicyTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(PolicyTests, self).setUp()
        self.additionalSetUp()
        self.key = 'policy'
        self.collection_key = 'policies'
        self.model = policies.Policy
        self.manager = self.client.policies

    def new_ref(self, **kwargs):
        kwargs = super(PolicyTests, self).new_ref(**kwargs)
        kwargs.setdefault('endpoint_id', uuid.uuid4().hex)
        kwargs.setdefault('type', uuid.uuid4().hex)
        kwargs.setdefault('blob', uuid.uuid4().hex)
        return kwargs
