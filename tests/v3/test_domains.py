import uuid

from keystoneclient.v3 import domains
from tests.v3 import utils


class DomainTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(DomainTests, self).setUp()
        self.additionalSetUp()
        self.key = 'domain'
        self.collection_key = 'domains'
        self.model = domains.Domain
        self.manager = self.client.domains

    def new_ref(self, **kwargs):
        kwargs = super(DomainTests, self).new_ref(**kwargs)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs
