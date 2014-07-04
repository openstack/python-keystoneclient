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

import abc
import uuid

import httpretty
import six

from keystoneclient.auth import base
from keystoneclient.auth.identity import v2
from keystoneclient.auth.identity import v3
from keystoneclient.openstack.common import jsonutils
from keystoneclient import session
from keystoneclient.tests import utils


@six.add_metaclass(abc.ABCMeta)
class CommonIdentityTests(object):

    TEST_ROOT_URL = 'http://127.0.0.1:5000/'
    TEST_ROOT_ADMIN_URL = 'http://127.0.0.1:35357/'

    TEST_COMPUTE_PUBLIC = 'http://nova/novapi/public'
    TEST_COMPUTE_INTERNAL = 'http://nova/novapi/internal'
    TEST_COMPUTE_ADMIN = 'http://nova/novapi/admin'

    TEST_PASS = uuid.uuid4().hex

    def setUp(self):
        super(CommonIdentityTests, self).setUp()

        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)

        self.TEST_URL = '%s%s' % (self.TEST_ROOT_URL, self.version)
        self.TEST_ADMIN_URL = '%s%s' % (self.TEST_ROOT_ADMIN_URL, self.version)

        disc_v2 = {
            'id': 'v2.0',
            'links': [
                {
                    'href': '%sv2.0' % self.TEST_ROOT_URL,
                    'rel': 'self'
                },
            ],
            'status': 'stable',
            'updated': '2014-04-17T00:00:00Z'
        }

        disc_v3 = {
            'id': 'v3.0',
            'links': [
                {
                    'href': '%sv3' % self.TEST_ROOT_URL,
                    'rel': 'self'
                }
            ],
            'status': 'stable',
            'updated': '2013-03-06T00:00:00Z'
        }

        self.TEST_DISCOVERY = {
            'versions': [disc_v2, disc_v3]
        }

        self.stub_auth_data()

    @abc.abstractmethod
    def create_auth_plugin(self):
        """Create an auth plugin that makes sense for the auth data.

        It doesn't really matter what auth mechanism is used but it should be
        appropriate to the API version.
        """

    @abc.abstractmethod
    def stub_auth_data(self):
        """Stub out authentication data.

        This should register a valid token response and ensure that the compute
        endpoints are set to TEST_COMPUTE_PUBLIC, _INTERNAL and _ADMIN.
        """

    @abc.abstractproperty
    def version(self):
        """The API version being tested."""

    def test_discovering(self):
        self.stub_url(httpretty.GET, [],
                      base_url=self.TEST_COMPUTE_ADMIN,
                      json=self.TEST_DISCOVERY)

        body = 'SUCCESS'

        # which gives our sample values
        self.stub_url(httpretty.GET, ['path'],
                      body=body, status=200)

        a = self.create_auth_plugin()
        s = session.Session(auth=a)

        resp = s.get('/path', endpoint_filter={'service_type': 'compute',
                                               'interface': 'admin',
                                               'version': self.version})

        self.assertEqual(200, resp.status_code)
        self.assertEqual(body, resp.text)

        new_body = 'SC SUCCESS'
        # if we don't specify a version, we use the URL from the SC
        self.stub_url(httpretty.GET, ['path'],
                      base_url=self.TEST_COMPUTE_ADMIN,
                      body=new_body, status=200)

        resp = s.get('/path', endpoint_filter={'service_type': 'compute',
                                               'interface': 'admin'})

        self.assertEqual(200, resp.status_code)
        self.assertEqual(new_body, resp.text)

    def test_discovery_uses_session_cache(self):
        # register responses such that if the discovery URL is hit more than
        # once then the response will be invalid and not point to COMPUTE_ADMIN
        disc_body = jsonutils.dumps(self.TEST_DISCOVERY)
        disc_responses = [httpretty.Response(body=disc_body, status=200),
                          httpretty.Response(body='', status=500)]
        httpretty.register_uri(httpretty.GET,
                               self.TEST_COMPUTE_ADMIN,
                               responses=disc_responses)

        body = 'SUCCESS'
        self.stub_url(httpretty.GET, ['path'], body=body, status=200)

        # now either of the two plugins I use, it should not cause a second
        # request to the discovery url.
        s = session.Session()
        a = self.create_auth_plugin()
        b = self.create_auth_plugin()

        for auth in (a, b):
            resp = s.get('/path',
                         auth=auth,
                         endpoint_filter={'service_type': 'compute',
                                          'interface': 'admin',
                                          'version': self.version})

            self.assertEqual(200, resp.status_code)
            self.assertEqual(body, resp.text)

    def test_discovery_uses_plugin_cache(self):
        # register responses such that if the discovery URL is hit more than
        # once then the response will be invalid and not point to COMPUTE_ADMIN
        disc_body = jsonutils.dumps(self.TEST_DISCOVERY)
        disc_responses = [httpretty.Response(body=disc_body, status=200),
                          httpretty.Response(body='', status=500)]
        httpretty.register_uri(httpretty.GET,
                               self.TEST_COMPUTE_ADMIN,
                               responses=disc_responses)

        body = 'SUCCESS'
        self.stub_url(httpretty.GET, ['path'], body=body, status=200)

        # now either of the two sessions I use, it should not cause a second
        # request to the discovery url.
        sa = session.Session()
        sb = session.Session()
        auth = self.create_auth_plugin()

        for sess in (sa, sb):
            resp = sess.get('/path',
                            auth=auth,
                            endpoint_filter={'service_type': 'compute',
                                             'interface': 'admin',
                                             'version': self.version})

            self.assertEqual(200, resp.status_code)
            self.assertEqual(body, resp.text)

    def test_discovering_with_no_data(self):
        # which returns discovery information pointing to TEST_URL but there is
        # no data there.
        self.stub_url(httpretty.GET, [],
                      base_url=self.TEST_COMPUTE_ADMIN,
                      status=400)

        # so the url that will be used is the same TEST_COMPUTE_ADMIN
        body = 'SUCCESS'
        self.stub_url(httpretty.GET, ['path'],
                      base_url=self.TEST_COMPUTE_ADMIN, body=body, status=200)

        a = self.create_auth_plugin()
        s = session.Session(auth=a)

        resp = s.get('/path', endpoint_filter={'service_type': 'compute',
                                               'interface': 'admin',
                                               'version': self.version})

        self.assertEqual(200, resp.status_code)
        self.assertEqual(body, resp.text)

    def test_asking_for_auth_endpoint_ignores_checks(self):
        a = self.create_auth_plugin()
        s = session.Session(auth=a)

        auth_url = s.get_endpoint(service_type='compute',
                                  interface=base.AUTH_INTERFACE)

        self.assertEqual(self.TEST_URL, auth_url)


class V3(CommonIdentityTests, utils.TestCase):

    @property
    def version(self):
        return 'v3'

    def stub_auth_data(self):
        service_catalog = [{
            'endpoints': [{
                'url': 'http://cdn.admin-nets.local:8774/v1.0/',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url': 'http://127.0.0.1:8774/v1.0',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url': 'http://cdn.admin-nets.local:8774/v1.0',
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'nova_compat'
        }, {
            'endpoints': [{
                'url': self.TEST_COMPUTE_PUBLIC,
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url': self.TEST_COMPUTE_INTERNAL,
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url': self.TEST_COMPUTE_ADMIN,
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'compute'
        }, {
            'endpoints': [{
                'url': 'http://glance/glanceapi/public',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url': 'http://glance/glanceapi/internal',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url': 'http://glance/glanceapi/admin',
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'image',
            'name': 'glance'
        }, {
            'endpoints': [{
                'url': 'http://127.0.0.1:5000/v3',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url': 'http://127.0.0.1:5000/v3',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url': self.TEST_ADMIN_URL,
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'identity'
        }, {
            'endpoints': [{
                'url': 'http://swift/swiftapi/public',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url': 'http://swift/swiftapi/internal',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url': 'http://swift/swiftapi/admin',
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'object-store'
        }]

        token = {
            'token': {
                'methods': [
                    'token',
                    'password'
                ],

                'expires_at': '2020-01-01T00:00:10.000123Z',
                'project': {
                    'domain': {
                        'id': self.TEST_DOMAIN_ID,
                        'name': self.TEST_DOMAIN_NAME
                    },
                    'id': self.TEST_TENANT_ID,
                    'name': self.TEST_TENANT_NAME
                },
                'user': {
                    'domain': {
                        'id': self.TEST_DOMAIN_ID,
                        'name': self.TEST_DOMAIN_NAME
                    },
                    'id': self.TEST_USER,
                    'name': self.TEST_USER
                },
                'issued_at': '2013-05-29T16:55:21.468960Z',
                'catalog': service_catalog
            },
        }

        self.stub_auth(json=token)

    def stub_auth(self, subject_token=None, **kwargs):
        if not subject_token:
            subject_token = self.TEST_TOKEN

        self.stub_url(httpretty.POST, ['auth', 'tokens'],
                      X_Subject_Token=subject_token, **kwargs)

    def create_auth_plugin(self):
        return v3.Password(self.TEST_URL,
                           username=self.TEST_USER,
                           password=self.TEST_PASS)


class V2(CommonIdentityTests, utils.TestCase):

    @property
    def version(self):
        return 'v2.0'

    def create_auth_plugin(self):
        return v2.Password(self.TEST_URL,
                           username=self.TEST_USER,
                           password=self.TEST_PASS)

    def stub_auth_data(self):
        service_catalog = [{
            'endpoints': [{
                'adminURL': 'http://cdn.admin-nets.local:8774/v1.0',
                'region': 'RegionOne',
                'internalURL': 'http://127.0.0.1:8774/v1.0',
                'publicURL': 'http://cdn.admin-nets.local:8774/v1.0/'
            }],
            'type': 'nova_compat',
            'name': 'nova_compat'
        }, {
            'endpoints': [{
                'adminURL': self.TEST_COMPUTE_ADMIN,
                'region': 'RegionOne',
                'internalURL': self.TEST_COMPUTE_INTERNAL,
                'publicURL': self.TEST_COMPUTE_PUBLIC
            }],
            'type': 'compute',
            'name': 'nova'
        }, {
            'endpoints': [{
                'adminURL': 'http://glance/glanceapi/admin',
                'region': 'RegionOne',
                'internalURL': 'http://glance/glanceapi/internal',
                'publicURL': 'http://glance/glanceapi/public'
            }],
            'type': 'image',
            'name': 'glance'
        }, {
            'endpoints': [{
                'adminURL': self.TEST_ADMIN_URL,
                'region': 'RegionOne',
                'internalURL': 'http://127.0.0.1:5000/v2.0',
                'publicURL': 'http://127.0.0.1:5000/v2.0'
            }],
            'type': 'identity',
            'name': 'keystone'
        }, {
            'endpoints': [{
                'adminURL': 'http://swift/swiftapi/admin',
                'region': 'RegionOne',
                'internalURL': 'http://swift/swiftapi/internal',
                'publicURL': 'http://swift/swiftapi/public'
            }],
            'type': 'object-store',
            'name': 'swift'
        }]

        token = {
            'access': {
                'token': {
                    'expires': '2020-01-01T00:00:10.000123Z',
                    'id': self.TEST_TOKEN,
                    'tenant': {
                        'id': self.TEST_TENANT_ID
                    },
                },
                'user': {
                    'id': self.TEST_USER
                },
                'serviceCatalog': service_catalog,
            },
        }

        self.stub_auth(json=token)

    def stub_auth(self, **kwargs):
        self.stub_url(httpretty.POST, ['tokens'], **kwargs)
