#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import unicode_literals


UNSCOPED_TOKEN = {
    'access': {'serviceCatalog': {},
               'token': {'expires': '2012-10-03T16:58:01Z',
                         'id': '3e2813b7ba0b4006840c3825860b86ed'},
               'user': {'id': 'c4da488862bd435c9e6c0275a0d0e49a',
                        'name': 'exampleuser',
                        'roles': [],
                        'roles_links': [],
                        'username': 'exampleuser'}
               }
}

_TENANT_ID = '225da22d3ce34b15877ea70b2a575f58'

PROJECT_SCOPED_TOKEN = {
    'access': {
        'serviceCatalog': [{
            'endpoints': [{
                'adminURL': 'http://admin:8776/v1/%s' % _TENANT_ID,
                'internalURL': 'http://internal:8776/v1/%s' % _TENANT_ID,
                'publicURL': 'http://public.com:8776/v1/%s' % _TENANT_ID,
                'region': 'RegionOne'
            }],
            'endpoints_links': [],
            'name': 'Volume Service',
            'type': 'volume'},
            {'endpoints': [{
                'adminURL': 'http://admin:9292/v1',
                'internalURL': 'http://internal:9292/v1',
                'publicURL': 'http://public.com:9292/v1',
                'region': 'RegionOne'
            }],
                'endpoints_links': [],
                'name': 'Image Service',
                'type': 'image'},
            {'endpoints': [{
                'adminURL': 'http://admin:8774/v2/%s' % _TENANT_ID,
                'internalURL': 'http://internal:8774/v2/%s' % _TENANT_ID,
                'publicURL': 'http://public.com:8774/v2/%s' % _TENANT_ID,
                'region': 'RegionOne'
            }],
                'endpoints_links': [],
                'name': 'Compute Service',
                'type': 'compute'},
            {'endpoints': [{
                'adminURL': 'http://admin:8773/services/Admin',
                'internalURL': 'http://internal:8773/services/Cloud',
                'publicURL': 'http://public.com:8773/services/Cloud',
                'region': 'RegionOne'
            }],
                'endpoints_links': [],
                'name': 'EC2 Service',
                'type': 'ec2'},
            {'endpoints': [{
                'adminURL': 'http://admin:35357/v2.0',
                'internalURL': 'http://internal:5000/v2.0',
                'publicURL': 'http://public.com:5000/v2.0',
                'region': 'RegionOne'
            }],
                'endpoints_links': [],
                'name': 'Identity Service',
                'type': 'identity'}],
        'token': {'expires': '2012-10-03T16:53:36Z',
                  'id': '04c7d5ffaeef485f9dc69c06db285bdb',
                  'tenant': {'description': '',
                             'enabled': True,
                             'id': '225da22d3ce34b15877ea70b2a575f58',
                             'name': 'exampleproject'}},
        'user': {'id': 'c4da488862bd435c9e6c0275a0d0e49a',
                 'name': 'exampleuser',
                 'roles': [{'id': 'edc12489faa74ee0aca0b8a0b4d74a74',
                            'name': 'Member'}],
                 'roles_links': [],
                 'username': 'exampleuser'}
    }
}

AUTH_RESPONSE_BODY = {
    'access': {
        'token': {
            'id': 'ab48a9efdfedb23ty3494',
            'expires': '2010-11-01T03:32:15-05:00',
            'tenant': {
                'id': '345',
                'name': 'My Project'
            }
        },
        'user': {
            'id': '123',
            'name': 'jqsmith',
            'roles': [{
                'id': '234',
                'name': 'compute:admin'
            }, {
                'id': '235',
                'name': 'object-store:admin',
                'tenantId': '1'
            }],
            'roles_links': []
        },
        'serviceCatalog': [{
            'name': 'Cloud Servers',
            'type': 'compute',
            'endpoints': [{
                'tenantId': '1',
                'publicURL': 'https://compute.north.host/v1/1234',
                'internalURL': 'https://compute.north.host/v1/1234',
                'region': 'North',
                'versionId': '1.0',
                'versionInfo': 'https://compute.north.host/v1.0/',
                'versionList': 'https://compute.north.host/'
            }, {
                'tenantId': '2',
                'publicURL': 'https://compute.north.host/v1.1/3456',
                'internalURL': 'https://compute.north.host/v1.1/3456',
                'region': 'North',
                'versionId': '1.1',
                'versionInfo': 'https://compute.north.host/v1.1/',
                'versionList': 'https://compute.north.host/'
            }],
            'endpoints_links': []
        }, {
            'name': 'Cloud Files',
            'type': 'object-store',
            'endpoints': [{
                'tenantId': '11',
                'publicURL': 'https://swift.north.host/v1/blah',
                'internalURL': 'https://swift.north.host/v1/blah',
                'region': 'South',
                'versionId': '1.0',
                'versionInfo': 'uri',
                'versionList': 'uri'
            }, {
                'tenantId': '2',
                'publicURL': 'https://swift.north.host/v1.1/blah',
                'internalURL': 'https://compute.north.host/v1.1/blah',
                'region': 'South',
                'versionId': '1.1',
                'versionInfo': 'https://swift.north.host/v1.1/',
                'versionList': 'https://swift.north.host/'
            }],
            'endpoints_links': [{
                'rel': 'next',
                'href': 'https://identity.north.host/v2.0/'
                        'endpoints?marker=2'
            }]
        }, {
            'name': 'Image Servers',
            'type': 'image',
            'endpoints': [{
                'publicURL': 'https://image.north.host/v1/',
                'internalURL': 'https://image-internal.north.host/v1/',
                'region': 'North'
            }, {
                'publicURL': 'https://image.south.host/v1/',
                'internalURL': 'https://image-internal.south.host/v1/',
                'region': 'South'
            }],
            'endpoints_links': []
        }],
        'serviceCatalog_links': [{
            'rel': 'next',
            'href': ('https://identity.host/v2.0/endpoints?'
                     'session=2hfh8Ar&marker=2')
        }]
    }
}
