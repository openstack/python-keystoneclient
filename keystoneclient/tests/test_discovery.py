# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import httpretty
import six
from testtools import matchers

from keystoneclient import _discover
from keystoneclient import client
from keystoneclient import discover
from keystoneclient import exceptions
from keystoneclient.openstack.common import jsonutils
from keystoneclient.tests import utils
from keystoneclient.v2_0 import client as v2_client
from keystoneclient.v3 import client as v3_client


BASE_HOST = 'http://keystone.example.com'
BASE_URL = "%s:5000/" % BASE_HOST
UPDATED = '2013-03-06T00:00:00Z'

TEST_SERVICE_CATALOG = [{
    "endpoints": [{
        "adminURL": "%s:8774/v1.0" % BASE_HOST,
        "region": "RegionOne",
        "internalURL": "%s://127.0.0.1:8774/v1.0" % BASE_HOST,
        "publicURL": "%s:8774/v1.0/" % BASE_HOST
    }],
    "type": "nova_compat",
    "name": "nova_compat"
}, {
    "endpoints": [{
        "adminURL": "http://nova/novapi/admin",
        "region": "RegionOne",
        "internalURL": "http://nova/novapi/internal",
        "publicURL": "http://nova/novapi/public"
    }],
    "type": "compute",
    "name": "nova"
}, {
    "endpoints": [{
        "adminURL": "http://glance/glanceapi/admin",
        "region": "RegionOne",
        "internalURL": "http://glance/glanceapi/internal",
        "publicURL": "http://glance/glanceapi/public"
    }],
    "type": "image",
    "name": "glance"
}, {
    "endpoints": [{
        "adminURL": "%s:35357/v2.0" % BASE_HOST,
        "region": "RegionOne",
        "internalURL": "%s:5000/v2.0" % BASE_HOST,
        "publicURL": "%s:5000/v2.0" % BASE_HOST
    }],
    "type": "identity",
    "name": "keystone"
}, {
    "endpoints": [{
        "adminURL": "http://swift/swiftapi/admin",
        "region": "RegionOne",
        "internalURL": "http://swift/swiftapi/internal",
        "publicURL": "http://swift/swiftapi/public"
    }],
    "type": "object-store",
    "name": "swift"
}]

V2_URL = "%sv2.0" % BASE_URL
V2_DESCRIBED_BY_HTML = {'href': 'http://docs.openstack.org/api/'
                                'openstack-identity-service/2.0/content/',
                        'rel': 'describedby',
                        'type': 'text/html'}
V2_DESCRIBED_BY_PDF = {'href': 'http://docs.openstack.org/api/openstack-ident'
                               'ity-service/2.0/identity-dev-guide-2.0.pdf',
                       'rel': 'describedby',
                       'type': 'application/pdf'}

V2_VERSION = {'id': 'v2.0',
              'links': [{'href': V2_URL, 'rel': 'self'},
                        V2_DESCRIBED_BY_HTML, V2_DESCRIBED_BY_PDF],
              'status': 'stable',
              'updated': UPDATED}

V2_AUTH_RESPONSE = jsonutils.dumps({
    "access": {
        "token": {
            "expires": "2020-01-01T00:00:10.000123Z",
            "id": 'fakeToken',
            "tenant": {
                "id": '1'
            },
        },
        "user": {
            "id": 'test'
        },
        "serviceCatalog": TEST_SERVICE_CATALOG,
    },
})

V3_URL = "%sv3" % BASE_URL
V3_MEDIA_TYPES = [{'base': 'application/json',
                   'type': 'application/vnd.openstack.identity-v3+json'},
                  {'base': 'application/xml',
                   'type': 'application/vnd.openstack.identity-v3+xml'}]

V3_VERSION = {'id': 'v3.0',
              'links': [{'href': V3_URL, 'rel': 'self'}],
              'media-types': V3_MEDIA_TYPES,
              'status': 'stable',
              'updated': UPDATED}

V3_TOKEN = u'3e2813b7ba0b4006840c3825860b86ed',
V3_AUTH_RESPONSE = jsonutils.dumps({
    "token": {
        "methods": [
            "token",
            "password"
        ],

        "expires_at": "2020-01-01T00:00:10.000123Z",
        "project": {
            "domain": {
                "id": '1',
                "name": 'test-domain'
            },
            "id": '1',
            "name": 'test-project'
        },
        "user": {
            "domain": {
                "id": '1',
                "name": 'test-domain'
            },
            "id": '1',
            "name": 'test-user'
        },
        "issued_at": "2013-05-29T16:55:21.468960Z",
    },
})

CINDER_EXAMPLES = {
    "versions": [
        {
            "status": "CURRENT",
            "updated": "2012-01-04T11:33:21Z",
            "id": "v1.0",
            "links": [
                {
                    "href": "%sv1/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "CURRENT",
            "updated": "2012-11-21T11:33:21Z",
            "id": "v2.0",
            "links": [
                {
                    "href": "%sv2/" % BASE_URL,
                    "rel": "self"
                }
            ]
        }
    ]
}

GLANCE_EXAMPLES = {
    "versions": [
        {
            "status": "CURRENT",
            "id": "v2.2",
            "links": [
                {
                    "href": "%sv2/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "SUPPORTED",
            "id": "v2.1",
            "links": [
                {
                    "href": "%sv2/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "SUPPORTED",
            "id": "v2.0",
            "links": [
                {
                    "href": "%sv2/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "CURRENT",
            "id": "v1.1",
            "links": [
                {
                    "href": "%sv1/" % BASE_URL,
                    "rel": "self"
                }
            ]
        },
        {
            "status": "SUPPORTED",
            "id": "v1.0",
            "links": [
                {
                    "href": "%sv1/" % BASE_URL,
                    "rel": "self"
                }
            ]
        }
    ]
}


def _create_version_list(versions):
    return jsonutils.dumps({'versions': {'values': versions}})


def _create_single_version(version):
    return jsonutils.dumps({'version': version})


V3_VERSION_LIST = _create_version_list([V3_VERSION, V2_VERSION])
V2_VERSION_LIST = _create_version_list([V2_VERSION])

V3_VERSION_ENTRY = _create_single_version(V3_VERSION)
V2_VERSION_ENTRY = _create_single_version(V2_VERSION)


@httpretty.activate
class AvailableVersionsTests(utils.TestCase):

    def test_available_versions_basics(self):
        examples = {'keystone': V3_VERSION_LIST,
                    'cinder': jsonutils.dumps(CINDER_EXAMPLES),
                    'glance': jsonutils.dumps(GLANCE_EXAMPLES)}

        for path, ex in six.iteritems(examples):
            url = "%s%s" % (BASE_URL, path)

            httpretty.register_uri(httpretty.GET, url, status=300, body=ex)
            versions = discover.available_versions(url)

            for v in versions:
                for n in ('id', 'status', 'links'):
                    msg = '%s missing from %s version data' % (n, path)
                    self.assertThat(v, matchers.Annotate(msg,
                                                         matchers.Contains(n)))

    def test_available_versions_individual(self):
        httpretty.register_uri(httpretty.GET, V3_URL, status=200,
                               body=V3_VERSION_ENTRY)

        versions = discover.available_versions(V3_URL)

        for v in versions:
            self.assertEqual(v['id'], 'v3.0')
            self.assertEqual(v['status'], 'stable')
            self.assertIn('media-types', v)
            self.assertIn('links', v)

    def test_available_keystone_data(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_LIST)

        versions = discover.available_versions(BASE_URL)
        self.assertEqual(2, len(versions))

        for v in versions:
            self.assertIn(v['id'], ('v2.0', 'v3.0'))
            self.assertEqual(v['updated'], UPDATED)
            self.assertEqual(v['status'], 'stable')

            if v['id'] == 'v3.0':
                self.assertEqual(v['media-types'], V3_MEDIA_TYPES)

    def test_available_cinder_data(self):
        body = jsonutils.dumps(CINDER_EXAMPLES)
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300, body=body)

        versions = discover.available_versions(BASE_URL)
        self.assertEqual(2, len(versions))

        for v in versions:
            self.assertEqual(v['status'], 'CURRENT')
            if v['id'] == 'v1.0':
                self.assertEqual(v['updated'], '2012-01-04T11:33:21Z')
            elif v['id'] == 'v2.0':
                self.assertEqual(v['updated'], '2012-11-21T11:33:21Z')
            else:
                self.fail("Invalid version found")

    def test_available_glance_data(self):
        body = jsonutils.dumps(GLANCE_EXAMPLES)
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200, body=body)

        versions = discover.available_versions(BASE_URL)
        self.assertEqual(5, len(versions))

        for v in versions:
            if v['id'] in ('v2.2', 'v1.1'):
                self.assertEqual(v['status'], 'CURRENT')
            elif v['id'] in ('v2.1', 'v2.0', 'v1.0'):
                self.assertEqual(v['status'], 'SUPPORTED')
            else:
                self.fail("Invalid version found")


@httpretty.activate
class ClientDiscoveryTests(utils.TestCase):

    def assertCreatesV3(self, **kwargs):
        httpretty.register_uri(httpretty.POST, "%s/auth/tokens" % V3_URL,
                               body=V3_AUTH_RESPONSE, X_Subject_Token=V3_TOKEN)

        kwargs.setdefault('username', 'foo')
        kwargs.setdefault('password', 'bar')
        keystone = client.Client(**kwargs)
        self.assertIsInstance(keystone, v3_client.Client)
        return keystone

    def assertCreatesV2(self, **kwargs):
        httpretty.register_uri(httpretty.POST, "%s/tokens" % V2_URL,
                               body=V2_AUTH_RESPONSE)

        kwargs.setdefault('username', 'foo')
        kwargs.setdefault('password', 'bar')
        keystone = client.Client(**kwargs)
        self.assertIsInstance(keystone, v2_client.Client)
        return keystone

    def assertVersionNotAvailable(self, **kwargs):
        kwargs.setdefault('username', 'foo')
        kwargs.setdefault('password', 'bar')

        self.assertRaises(exceptions.VersionNotAvailable,
                          client.Client, **kwargs)

    def assertDiscoveryFailure(self, **kwargs):
        kwargs.setdefault('username', 'foo')
        kwargs.setdefault('password', 'bar')

        self.assertRaises(exceptions.DiscoveryFailure,
                          client.Client, **kwargs)

    def test_discover_v3(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_LIST)

        self.assertCreatesV3(auth_url=BASE_URL)

    def test_discover_v2(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V2_VERSION_LIST)
        httpretty.register_uri(httpretty.POST, "%s/tokens" % V2_URL,
                               body=V2_AUTH_RESPONSE)

        self.assertCreatesV2(auth_url=BASE_URL)

    def test_discover_endpoint_v2(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V2_VERSION_LIST)
        self.assertCreatesV2(endpoint=BASE_URL, token='fake-token')

    def test_discover_endpoint_v3(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_LIST)
        self.assertCreatesV3(endpoint=BASE_URL, token='fake-token')

    def test_discover_invalid_major_version(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_LIST)

        self.assertVersionNotAvailable(auth_url=BASE_URL, version=5)

    def test_discover_200_response_fails(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200, body='ok')
        self.assertDiscoveryFailure(auth_url=BASE_URL)

    def test_discover_minor_greater_than_available_fails(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_LIST)

        self.assertVersionNotAvailable(endpoint=BASE_URL, version=3.4)

    def test_discover_individual_version_v2(self):
        httpretty.register_uri(httpretty.GET, V2_URL, status=200,
                               body=V2_VERSION_ENTRY)

        self.assertCreatesV2(auth_url=V2_URL)

    def test_discover_individual_version_v3(self):
        httpretty.register_uri(httpretty.GET, V3_URL, status=200,
                               body=V3_VERSION_ENTRY)

        self.assertCreatesV3(auth_url=V3_URL)

    def test_discover_individual_endpoint_v2(self):
        httpretty.register_uri(httpretty.GET, V2_URL, status=200,
                               body=V2_VERSION_ENTRY)
        self.assertCreatesV2(endpoint=V2_URL, token='fake-token')

    def test_discover_individual_endpoint_v3(self):
        httpretty.register_uri(httpretty.GET, V3_URL, status=200,
                               body=V3_VERSION_ENTRY)
        self.assertCreatesV3(endpoint=V3_URL, token='fake-token')

    def test_discover_fail_to_create_bad_individual_version(self):
        httpretty.register_uri(httpretty.GET, V2_URL, status=200,
                               body=V2_VERSION_ENTRY)
        httpretty.register_uri(httpretty.GET, V3_URL, status=200,
                               body=V3_VERSION_ENTRY)

        self.assertVersionNotAvailable(auth_url=V2_URL, version=3)
        self.assertVersionNotAvailable(auth_url=V3_URL, version=2)

    def test_discover_unstable_versions(self):
        v3_unstable_version = V3_VERSION.copy()
        v3_unstable_version['status'] = 'beta'
        version_list = _create_version_list([v3_unstable_version, V2_VERSION])

        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=version_list)

        self.assertCreatesV2(auth_url=BASE_URL)
        self.assertVersionNotAvailable(auth_url=BASE_URL, version=3)
        self.assertCreatesV3(auth_url=BASE_URL, unstable=True)

    def test_discover_forwards_original_ip(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_LIST)

        ip = '192.168.1.1'
        self.assertCreatesV3(auth_url=BASE_URL, original_ip=ip)

        self.assertThat(httpretty.last_request().headers['forwarded'],
                        matchers.Contains(ip))

    def test_discover_bad_args(self):
        self.assertRaises(exceptions.DiscoveryFailure,
                          client.Client)

    def test_discover_bad_response(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=jsonutils.dumps({'FOO': 'BAR'}))
        self.assertDiscoveryFailure(auth_url=BASE_URL)

    def test_discovery_ignore_invalid(self):
        resp = [{'id': 'v3.0',
                 'links': [1, 2, 3, 4],  # invalid links
                 'media-types': V3_MEDIA_TYPES,
                 'status': 'stable',
                 'updated': UPDATED}]
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=_create_version_list(resp))
        self.assertDiscoveryFailure(auth_url=BASE_URL)

    def test_ignore_entry_without_links(self):
        v3 = V3_VERSION.copy()
        v3['links'] = []
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=_create_version_list([v3, V2_VERSION]))
        self.assertCreatesV2(auth_url=BASE_URL)

    def test_ignore_entry_without_status(self):
        v3 = V3_VERSION.copy()
        del v3['status']
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=_create_version_list([v3, V2_VERSION]))
        self.assertCreatesV2(auth_url=BASE_URL)

    def test_greater_version_than_required(self):
        resp = [{'id': 'v3.6',
                 'links': [{'href': V3_URL, 'rel': 'self'}],
                 'media-types': V3_MEDIA_TYPES,
                 'status': 'stable',
                 'updated': UPDATED}]
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200,
                               body=_create_version_list(resp))
        self.assertCreatesV3(auth_url=BASE_URL, version=(3, 4))

    def test_lesser_version_than_required(self):
        resp = [{'id': 'v3.4',
                 'links': [{'href': V3_URL, 'rel': 'self'}],
                 'media-types': V3_MEDIA_TYPES,
                 'status': 'stable',
                 'updated': UPDATED}]
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200,
                               body=_create_version_list(resp))
        self.assertVersionNotAvailable(auth_url=BASE_URL, version=(3, 6))

    def test_bad_response(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body="Ugly Duckling")
        self.assertDiscoveryFailure(auth_url=BASE_URL)

    def test_pass_client_arguments(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V2_VERSION_LIST)
        kwargs = {'original_ip': '100', 'use_keyring': False,
                  'stale_duration': 15}

        cl = self.assertCreatesV2(auth_url=BASE_URL, **kwargs)

        self.assertEqual(cl.original_ip, '100')
        self.assertEqual(cl.stale_duration, 15)
        self.assertFalse(cl.use_keyring)

    def test_overriding_stored_kwargs(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_LIST)

        httpretty.register_uri(httpretty.POST, "%s/auth/tokens" % V3_URL,
                               body=V3_AUTH_RESPONSE, X_Subject_Token=V3_TOKEN)

        disc = discover.Discover(auth_url=BASE_URL, debug=False,
                                 username='foo')
        client = disc.create_client(debug=True, password='bar')

        self.assertIsInstance(client, v3_client.Client)
        self.assertTrue(client.debug_log)
        self.assertFalse(disc._client_kwargs['debug'])
        self.assertEqual(client.username, 'foo')
        self.assertEqual(client.password, 'bar')

    def test_available_versions(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_ENTRY)
        disc = discover.Discover(auth_url=BASE_URL)

        versions = disc.available_versions()
        self.assertEqual(1, len(versions))
        self.assertEqual(V3_VERSION, versions[0])

    def test_unknown_client_version(self):
        V4_VERSION = {'id': 'v4.0',
                      'links': [{'href': 'http://url', 'rel': 'self'}],
                      'media-types': V3_MEDIA_TYPES,
                      'status': 'stable',
                      'updated': UPDATED}
        body = _create_version_list([V4_VERSION, V3_VERSION, V2_VERSION])
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300, body=body)

        disc = discover.Discover(auth_url=BASE_URL)
        self.assertRaises(exceptions.DiscoveryFailure,
                          disc.create_client, version=4)


@httpretty.activate
class DiscoverQueryTests(utils.TestCase):

    def test_available_keystone_data(self):
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300,
                               body=V3_VERSION_LIST)

        disc = discover.Discover(auth_url=BASE_URL)
        versions = disc.version_data()

        self.assertEqual((2, 0), versions[0]['version'])
        self.assertEqual('stable', versions[0]['raw_status'])
        self.assertEqual(V2_URL, versions[0]['url'])
        self.assertEqual((3, 0), versions[1]['version'])
        self.assertEqual('stable', versions[1]['raw_status'])
        self.assertEqual(V3_URL, versions[1]['url'])

        version = disc.data_for('v3.0')
        self.assertEqual((3, 0), version['version'])
        self.assertEqual('stable', version['raw_status'])
        self.assertEqual(V3_URL, version['url'])

        version = disc.data_for(2)
        self.assertEqual((2, 0), version['version'])
        self.assertEqual('stable', version['raw_status'])
        self.assertEqual(V2_URL, version['url'])

        self.assertIsNone(disc.url_for('v4'))
        self.assertEqual(V3_URL, disc.url_for('v3'))
        self.assertEqual(V2_URL, disc.url_for('v2'))

    def test_available_cinder_data(self):
        body = jsonutils.dumps(CINDER_EXAMPLES)
        httpretty.register_uri(httpretty.GET, BASE_URL, status=300, body=body)

        v1_url = "%sv1/" % BASE_URL
        v2_url = "%sv2/" % BASE_URL

        disc = discover.Discover(auth_url=BASE_URL)
        versions = disc.version_data()

        self.assertEqual((1, 0), versions[0]['version'])
        self.assertEqual('CURRENT', versions[0]['raw_status'])
        self.assertEqual(v1_url, versions[0]['url'])
        self.assertEqual((2, 0), versions[1]['version'])
        self.assertEqual('CURRENT', versions[1]['raw_status'])
        self.assertEqual(v2_url, versions[1]['url'])

        version = disc.data_for('v2.0')
        self.assertEqual((2, 0), version['version'])
        self.assertEqual('CURRENT', version['raw_status'])
        self.assertEqual(v2_url, version['url'])

        version = disc.data_for(1)
        self.assertEqual((1, 0), version['version'])
        self.assertEqual('CURRENT', version['raw_status'])
        self.assertEqual(v1_url, version['url'])

        self.assertIsNone(disc.url_for('v3'))
        self.assertEqual(v2_url, disc.url_for('v2'))
        self.assertEqual(v1_url, disc.url_for('v1'))

    def test_available_glance_data(self):
        body = jsonutils.dumps(GLANCE_EXAMPLES)
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200, body=body)

        v1_url = "%sv1/" % BASE_URL
        v2_url = "%sv2/" % BASE_URL

        disc = discover.Discover(auth_url=BASE_URL)
        versions = disc.version_data()

        self.assertEqual((1, 0), versions[0]['version'])
        self.assertEqual('SUPPORTED', versions[0]['raw_status'])
        self.assertEqual(v1_url, versions[0]['url'])
        self.assertEqual((1, 1), versions[1]['version'])
        self.assertEqual('CURRENT', versions[1]['raw_status'])
        self.assertEqual(v1_url, versions[1]['url'])
        self.assertEqual((2, 0), versions[2]['version'])
        self.assertEqual('SUPPORTED', versions[2]['raw_status'])
        self.assertEqual(v2_url, versions[2]['url'])
        self.assertEqual((2, 1), versions[3]['version'])
        self.assertEqual('SUPPORTED', versions[3]['raw_status'])
        self.assertEqual(v2_url, versions[3]['url'])
        self.assertEqual((2, 2), versions[4]['version'])
        self.assertEqual('CURRENT', versions[4]['raw_status'])
        self.assertEqual(v2_url, versions[4]['url'])

        for ver in (2, 2.1, 2.2):
            version = disc.data_for(ver)
            self.assertEqual((2, 2), version['version'])
            self.assertEqual('CURRENT', version['raw_status'])
            self.assertEqual(v2_url, version['url'])
            self.assertEqual(v2_url, disc.url_for(ver))

        for ver in (1, 1.1):
            version = disc.data_for(ver)
            self.assertEqual((1, 1), version['version'])
            self.assertEqual('CURRENT', version['raw_status'])
            self.assertEqual(v1_url, version['url'])
            self.assertEqual(v1_url, disc.url_for(ver))

        self.assertIsNone(disc.url_for('v3'))
        self.assertIsNone(disc.url_for('v2.3'))

    def test_allow_deprecated(self):
        status = 'deprecated'
        version_list = [{'id': 'v3.0',
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         'media-types': V3_MEDIA_TYPES,
                         'status': status,
                         'updated': UPDATED}]
        body = jsonutils.dumps({'versions': version_list})
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200, body=body)

        disc = discover.Discover(auth_url=BASE_URL)

        # deprecated is allowed by default
        versions = disc.version_data(allow_deprecated=False)
        self.assertEqual(0, len(versions))

        versions = disc.version_data(allow_deprecated=True)
        self.assertEqual(1, len(versions))
        self.assertEqual(status, versions[0]['raw_status'])
        self.assertEqual(V3_URL, versions[0]['url'])
        self.assertEqual((3, 0), versions[0]['version'])

    def test_allow_experimental(self):
        status = 'experimental'
        version_list = [{'id': 'v3.0',
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         'media-types': V3_MEDIA_TYPES,
                         'status': status,
                         'updated': UPDATED}]
        body = jsonutils.dumps({'versions': version_list})
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200, body=body)

        disc = discover.Discover(auth_url=BASE_URL)

        versions = disc.version_data()
        self.assertEqual(0, len(versions))

        versions = disc.version_data(allow_experimental=True)
        self.assertEqual(1, len(versions))
        self.assertEqual(status, versions[0]['raw_status'])
        self.assertEqual(V3_URL, versions[0]['url'])
        self.assertEqual((3, 0), versions[0]['version'])

    def test_allow_unknown(self):
        status = 'abcdef'
        version_list = [{'id': 'v3.0',
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         'media-types': V3_MEDIA_TYPES,
                         'status': status,
                         'updated': UPDATED}]
        body = jsonutils.dumps({'versions': version_list})
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200, body=body)

        disc = discover.Discover(auth_url=BASE_URL)

        versions = disc.version_data()
        self.assertEqual(0, len(versions))

        versions = disc.version_data(allow_unknown=True)
        self.assertEqual(1, len(versions))
        self.assertEqual(status, versions[0]['raw_status'])
        self.assertEqual(V3_URL, versions[0]['url'])
        self.assertEqual((3, 0), versions[0]['version'])

    def test_ignoring_invalid_lnks(self):
        version_list = [{'id': 'v3.0',
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         'media-types': V3_MEDIA_TYPES,
                         'status': 'stable',
                         'updated': UPDATED},
                        {'id': 'v3.1',
                         'media-types': V3_MEDIA_TYPES,
                         'status': 'stable',
                         'updated': UPDATED},
                        {'media-types': V3_MEDIA_TYPES,
                         'status': 'stable',
                         'updated': UPDATED,
                         'links': [{'href': V3_URL, 'rel': 'self'}],
                         }]

        body = jsonutils.dumps({'versions': version_list})
        httpretty.register_uri(httpretty.GET, BASE_URL, status=200, body=body)

        disc = discover.Discover(auth_url=BASE_URL)

        # raw_version_data will return all choices, even invalid ones
        versions = disc.raw_version_data()
        self.assertEqual(3, len(versions))

        # only the version with both id and links will be actually returned
        versions = disc.version_data()
        self.assertEqual(1, len(versions))


class DiscoverUtils(utils.TestCase):

    def test_version_number(self):
        def assertVersion(inp, out):
            self.assertEqual(out, _discover.normalize_version_number(inp))

        def versionRaises(inp):
            self.assertRaises(TypeError,
                              _discover.normalize_version_number,
                              inp)

        assertVersion('v1.2', (1, 2))
        assertVersion('v11', (11, 0))
        assertVersion('1.2', (1, 2))
        assertVersion('1.5.1', (1, 5, 1))
        assertVersion('1', (1, 0))
        assertVersion(1, (1, 0))
        assertVersion(5.2, (5, 2))
        assertVersion((6, 1), (6, 1))
        assertVersion([1, 4], (1, 4))

        versionRaises('hello')
        versionRaises('1.a')
        versionRaises('vacuum')
