# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
    'token': {
        'methods': [
            'password'
        ],
        'catalog': {},
        'expires_at': '2010-11-01T03:32:15-05:00',
        'user': {
            'domain': {
                'id': '4e6893b7ba0b4006840c3845660b86ed',
                'name': 'exampledomain'
            },
            'id': 'c4da488862bd435c9e6c0275a0d0e49a',
            'name': 'exampleuser',
        }
    }
}

DOMAIN_SCOPED_TOKEN = {
    'token': {
        'methods': [
            'password'
        ],
        'catalog': {},
        'expires_at': '2010-11-01T03:32:15-05:00',
        'user': {
            'domain': {
                'id': '4e6893b7ba0b4006840c3845660b86ed',
                'name': 'exampledomain'
            },
            'id': 'c4da488862bd435c9e6c0275a0d0e49a',
            'name': 'exampleuser',
        },
        'domain': {
            'id': '8e9283b7ba0b1038840c3842058b86ab',
            'name': 'anotherdomain'
        },
    }
}

PROJECT_SCOPED_TOKEN = {
    'token': {
        'methods': [
            'password'
        ],
        'catalog': [{
            'endpoints': [{
                'url':
                'http://public.com:8776/v1/225da22d3ce34b15877ea70b2a575f58',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url':
                'http://internal:8776/v1/225da22d3ce34b15877ea70b2a575f58',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url':
                'http://admin:8776/v1/225da22d3ce34b15877ea70b2a575f58',
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'volume'
        }, {
            'endpoints': [{
                'url': 'http://public.com:9292/v1',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url': 'http://internal:9292/v1',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url': 'http://admin:9292/v1',
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'image'
        }, {
            'endpoints': [{
                'url':
                'http://public.com:8774/v2/225da22d3ce34b15877ea70b2a575f58',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url':
                'http://internal:8774/v2/225da22d3ce34b15877ea70b2a575f58',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url':
                'http://admin:8774/v2/225da22d3ce34b15877ea70b2a575f58',
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'compute'
        }, {
            'endpoints': [{
                'url': 'http://public.com:8773/services/Cloud',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url': 'http://internal:8773/services/Cloud',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url': 'http://admin:8773/services/Admin',
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'ec2'
        }, {
            'endpoints': [{
                'url': 'http://public.com:5000/v3',
                'region': 'RegionOne',
                'interface': 'public'
            }, {
                'url': 'http://internal:5000/v3',
                'region': 'RegionOne',
                'interface': 'internal'
            }, {
                'url': 'http://admin:35357/v3',
                'region': 'RegionOne',
                'interface': 'admin'
            }],
            'type': 'identity'
        }],
        'expires_at': '2010-11-01T03:32:15-05:00',
        'user': {
            'domain': {
                'id': '4e6893b7ba0b4006840c3845660b86ed',
                'name': 'exampledomain'
            },
            'id': 'c4da488862bd435c9e6c0275a0d0e49a',
            'name': 'exampleuser',
        },
        'project': {
            'domain': {
                'id': '4e6893b7ba0b4006840c3845660b86ed',
                'name': 'exampledomain'
            },
            'id': '225da22d3ce34b15877ea70b2a575f58',
            'name': 'exampleproject',
        },
    }
}

AUTH_SUBJECT_TOKEN = '3e2813b7ba0b4006840c3825860b86ed'

AUTH_RESPONSE_HEADERS = {
    'X-Subject-Token': AUTH_SUBJECT_TOKEN
}

AUTH_RESPONSE_BODY = {
    'token': {
        'methods': [
            'password'
        ],
        'expires_at': '2010-11-01T03:32:15-05:00',
        'project': {
            'domain': {
                'id': '123',
                'name': 'aDomain'
            },
            'id': '345',
            'name': 'aTenant'
        },
        'user': {
            'domain': {
                'id': '1',
                'name': 'aDomain'
            },
            'id': '567',
            'name': 'test'
        },
        'issued_at': '2010-10-31T03:32:15-05:00',
        'catalog': [{
            'endpoints': [{
                'url': 'https://compute.north.host/novapi/public',
                'region': 'North',
                'interface': 'public'
            }, {
                'url': 'https://compute.north.host/novapi/internal',
                'region': 'North',
                'interface': 'internal'
            }, {
                'url': 'https://compute.north.host/novapi/admin',
                'region': 'North',
                'interface': 'admin'
            }],
            'type': 'compute'
        }, {
            'endpoints': [{
                'url': 'http://swift.north.host/swiftapi/public',
                'region': 'South',
                'interface': 'public'
            }, {
                'url': 'http://swift.north.host/swiftapi/internal',
                'region': 'South',
                'interface': 'internal'
            }, {
                'url': 'http://swift.north.host/swiftapi/admin',
                'region': 'South',
                'interface': 'admin'
            }],
            'type': 'object-store'
        }, {
            'endpoints': [{
                'url': 'http://glance.north.host/glanceapi/public',
                'region': 'North',
                'interface': 'public'
            }, {
                'url': 'http://glance.north.host/glanceapi/internal',
                'region': 'North',
                'interface': 'internal'
            }, {
                'url': 'http://glance.north.host/glanceapi/admin',
                'region': 'North',
                'interface': 'admin'
            }, {
                'url': 'http://glance.south.host/glanceapi/public',
                'region': 'South',
                'interface': 'public'
            }, {
                'url': 'http://glance.south.host/glanceapi/internal',
                'region': 'South',
                'interface': 'internal'
            }, {
                'url': 'http://glance.south.host/glanceapi/admin',
                'region': 'South',
                'interface': 'admin'
            }],
            'type': 'image'
        }]
    }
}

TRUST_TOKEN = {
    'token': {
        'methods': [
            'password'
        ],
        'catalog': {},
        'expires_at': '2010-11-01T03:32:15-05:00',
        "OS-TRUST:trust": {
            "id": "fe0aef",
            "impersonation": False,
            "links": {
                "self": "http://identity:35357/v3/trusts/fe0aef"
            },
            "trustee_user": {
                "id": "0ca8f6",
                "links": {
                    "self": "http://identity:35357/v3/users/0ca8f6"
                }
            },
            "trustor_user": {
                "id": "bd263c",
                "links": {
                    "self": "http://identity:35357/v3/users/bd263c"
                }
            }
        },
        'user': {
            'domain': {
                'id': '4e6893b7ba0b4006840c3845660b86ed',
                'name': 'exampledomain'
            },
            'id': '0ca8f6',
            'name': 'exampleuser',
        }
    }
}
