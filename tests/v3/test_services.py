import uuid

from keystoneclient.v3 import services
from tests.v3 import utils


class ServiceTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(ServiceTests, self).setUp()
        self.additionalSetUp()
        self.key = 'service'
        self.collection_key = 'services'
        self.model = services.Service
        self.manager = self.client.services

    def new_ref(self, **kwargs):
        kwargs = super(ServiceTests, self).new_ref(**kwargs)
        kwargs.setdefault('name', uuid.uuid4().hex)
        kwargs.setdefault('type', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        return kwargs
