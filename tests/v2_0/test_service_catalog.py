from keystoneclient import access
from keystoneclient import exceptions

from tests import utils
from tests.v2_0 import client_fixtures


class ServiceCatalogTest(utils.TestCase):
    def setUp(self):
        super(ServiceCatalogTest, self).setUp()
        self.AUTH_RESPONSE_BODY = client_fixtures.AUTH_RESPONSE_BODY

    def test_building_a_service_catalog(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        self.assertEquals(sc.url_for(service_type='compute'),
                          "https://compute.north.host/v1/1234")
        self.assertEquals(sc.url_for('tenantId', '1', service_type='compute'),
                          "https://compute.north.host/v1/1234")
        self.assertEquals(sc.url_for('tenantId', '2', service_type='compute'),
                          "https://compute.north.host/v1.1/3456")

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for, "region",
                          "South", service_type='compute')

    def test_service_catalog_endpoints(self):
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog
        public_ep = sc.get_endpoints(service_type='compute',
                                     endpoint_type='publicURL')
        self.assertEquals(public_ep['compute'][1]['tenantId'], '2')
        self.assertEquals(public_ep['compute'][1]['versionId'], '1.1')
        self.assertEquals(public_ep['compute'][1]['internalURL'],
                          "https://compute.north.host/v1.1/3456")

    def test_service_catalog_regions(self):
        self.AUTH_RESPONSE_BODY['access']['region_name'] = "North"
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', endpoint_type='publicURL')
        self.assertEquals(url, "https://image.north.host/v1/")

        self.AUTH_RESPONSE_BODY['access']['region_name'] = "South"
        auth_ref = access.AccessInfo.factory(None, self.AUTH_RESPONSE_BODY)
        sc = auth_ref.service_catalog

        url = sc.url_for(service_type='image', endpoint_type='internalURL')
        self.assertEquals(url, "https://image-internal.south.host/v1/")
