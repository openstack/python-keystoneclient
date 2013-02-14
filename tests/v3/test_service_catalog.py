from keystoneclient import access
from keystoneclient import exceptions

from tests.v3 import client_fixtures
from tests.v3 import utils


class ServiceCatalogTest(utils.TestCase):
    def setUp(self):
        super(ServiceCatalogTest, self).setUp()
        self.AUTH_RESPONSE_BODY = client_fixtures.AUTH_RESPONSE_BODY
        self.RESPONSE = utils.TestResponse({
            "headers": client_fixtures.AUTH_RESPONSE_HEADERS
        })

    def test_building_a_service_catalog(self):
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        self.assertEquals(sc.url_for(service_type='compute'),
                          "https://compute.north.host/novapi/public")
        self.assertEquals(sc.url_for(service_type='compute',
                                     endpoint_type='internal'),
                          "https://compute.north.host/novapi/internal")

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for, "region",
                          "South", service_type='compute')

    def test_service_catalog_endpoints(self):
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        public_ep = sc.get_endpoints(service_type='compute',
                                     endpoint_type='public')
        self.assertEquals(public_ep['compute'][0]['region'], 'North')
        self.assertEquals(public_ep['compute'][0]['url'],
                          "https://compute.north.host/novapi/public")

    def test_service_catalog_regions(self):
        self.AUTH_RESPONSE_BODY['token']['region_name'] = "North"
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', endpoint_type='public')
        self.assertEquals(url, "http://glance.north.host/glanceapi/public")

        self.AUTH_RESPONSE_BODY['token']['region_name'] = "South"
        auth_ref = access.AccessInfo.factory(self.RESPONSE,
                                             self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog
        url = sc.url_for(service_type='image', endpoint_type='internal')
        self.assertEquals(url, "http://glance.south.host/glanceapi/internal")
