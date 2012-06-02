from keystoneclient import exceptions
from keystoneclient import service_catalog
from tests import utils


# Taken directly from keystone/content/common/samples/auth.json
# Do not edit this structure. Instead, grab the latest from there.

SERVICE_CATALOG = {
    "access": {
        "token": {
            "id": "ab48a9efdfedb23ty3494",
            "expires": "2010-11-01T03:32:15-05:00",
            "tenant": {
                "id": "345",
                "name": "My Project"
            }
        },
        "user": {
            "id": "123",
            "name": "jqsmith",
            "roles": [{
                "id": "234",
                "name": "compute:admin"
            },
            {
                "id": "235",
                "name": "object-store:admin",
                "tenantId": "1"
            }],
            "roles_links": []
        },
        "serviceCatalog": [{
            "name": "Cloud Servers",
            "type": "compute",
            "endpoints": [{
                "tenantId": "1",
                "publicURL": "https://compute.north.host/v1/1234",
                "internalURL": "https://compute.north.host/v1/1234",
                "region": "North",
                "versionId": "1.0",
                "versionInfo": "https://compute.north.host/v1.0/",
                "versionList": "https://compute.north.host/"
            },
            {
                "tenantId": "2",
                "publicURL": "https://compute.north.host/v1.1/3456",
                "internalURL": "https://compute.north.host/v1.1/3456",
                "region": "North",
                "versionId": "1.1",
                "versionInfo": "https://compute.north.host/v1.1/",
                "versionList": "https://compute.north.host/"
            }],
            "endpoints_links": []
        },
            {
                "name": "Cloud Files",
                "type": "object-store",
                "endpoints": [{
                    "tenantId": "11",
                    "publicURL": "https://compute.north.host/v1/blah-blah",
                    "internalURL": "https://compute.north.host/v1/blah-blah",
                    "region": "South",
                    "versionId": "1.0",
                    "versionInfo": "uri",
                    "versionList": "uri"
                },
                {
                    "tenantId": "2",
                    "publicURL": "https://compute.north.host/v1.1/blah-blah",
                    "internalURL": "https://compute.north.host/v1.1/blah-blah",
                    "region": "South",
                    "versionId": "1.1",
                    "versionInfo": "https://compute.north.host/v1.1/",
                    "versionList": "https://compute.north.host/"
                }],
                "endpoints_links":[{
                    "rel":"next",
                    "href":"https://identity.north.host/v2.0/"
                           "endpoints?marker=2"
                }]
            }
        ],
        "serviceCatalog_links": [{
            "rel": "next",
            "href": ("https://identity.host/v2.0/endpoints?"
                     "session=2hfh8Ar&marker=2")
        }]
    }
}


class ServiceCatalogTest(utils.TestCase):
    def test_building_a_service_catalog(self):
        sc = service_catalog.ServiceCatalog(SERVICE_CATALOG['access'])

        self.assertEquals(sc.url_for(service_type='compute'),
                            "https://compute.north.host/v1/1234")
        self.assertEquals(sc.url_for('tenantId', '1', service_type='compute'),
                            "https://compute.north.host/v1/1234")
        self.assertEquals(sc.url_for('tenantId', '2', service_type='compute'),
                            "https://compute.north.host/v1.1/3456")

        self.assertRaises(exceptions.EndpointNotFound, sc.url_for, "region",
                          "South", service_type='compute')

    def test_service_catalog_endpoints(self):
        sc = service_catalog.ServiceCatalog(SERVICE_CATALOG['access'])
        public_ep = sc.get_endpoints(service_type='compute',
                                     endpoint_type='publicURL')
        self.assertEquals(public_ep['compute'][1]['tenantId'], '2')
        self.assertEquals(public_ep['compute'][1]['versionId'], '1.1')
        self.assertEquals(public_ep['compute'][1]['internalURL'],
                          "https://compute.north.host/v1.1/3456")

    def test_token(self):
        sc = service_catalog.ServiceCatalog(SERVICE_CATALOG['access'])

        self.assertEquals(sc.get_token(), {
            'id': 'ab48a9efdfedb23ty3494',
            'tenant_id': '345',
            'user_id': '123',
            'expires': '2010-11-01T03:32:15-05:00'})
        self.assertEquals(sc.catalog['token']['expires'],
                          "2010-11-01T03:32:15-05:00")
        self.assertEquals(sc.catalog['token']['tenant']['id'], '345')
