UNSCOPED_TOKEN = {
    u'token': {
        u'methods': [
            u'password'
        ],
        u'catalog': {},
        u'expires_at': u'2010-11-01T03:32:15-05:00',
        u'user': {
            u'domain': {
                u'id': u'4e6893b7ba0b4006840c3845660b86ed',
                u'name': u'exampledomain'
            },
            u'id': u'c4da488862bd435c9e6c0275a0d0e49a',
            u'name': u'exampleuser',
        }
    }
}

DOMAIN_SCOPED_TOKEN = {
    u'token': {
        u'methods': [
            u'password'
        ],
        u'catalog': {},
        u'expires_at': u'2010-11-01T03:32:15-05:00',
        u'user': {
            u'domain': {
                u'id': u'4e6893b7ba0b4006840c3845660b86ed',
                u'name': u'exampledomain'
            },
            u'id': u'c4da488862bd435c9e6c0275a0d0e49a',
            u'name': u'exampleuser',
        },
        u'domain': {
            u'id': u'8e9283b7ba0b1038840c3842058b86ab',
            u'name': u'anotherdomain'
        },
    }
}

PROJECT_SCOPED_TOKEN = {
    u'token': {
        u'methods': [
            u'password'
        ],
        u'catalog': [{
            u'endpoints': [{
                u'url':
                u'http://public.com:8776/v1/225da22d3ce34b15877ea70b2a575f58',
                u'region': u'RegionOne',
                u'interface': u'public'
            }, {
                u'url':
                u'http://internal:8776/v1/225da22d3ce34b15877ea70b2a575f58',
                u'region': u'RegionOne',
                u'interface': u'internal'
            }, {
                u'url':
                u'http://admin:8776/v1/225da22d3ce34b15877ea70b2a575f58',
                u'region': u'RegionOne',
                u'interface': u'admin'
            }],
            u'type': u'volume'
        }, {
            u'endpoints': [{
                u'url': u'http://public.com:9292/v1',
                u'region': u'RegionOne',
                u'interface': u'public'
            }, {
                u'url': u'http://internal:9292/v1',
                u'region': u'RegionOne',
                u'interface': u'internal'
            }, {
                u'url': u'http://admin:9292/v1',
                u'region': u'RegionOne',
                u'interface': u'admin'
            }],
            u'type': u'image'
        }, {
            u'endpoints': [{
                u'url':
                u'http://public.com:8774/v2/225da22d3ce34b15877ea70b2a575f58',
                u'region': u'RegionOne',
                u'interface': u'public'
            }, {
                u'url':
                u'http://internal:8774/v2/225da22d3ce34b15877ea70b2a575f58',
                u'region': u'RegionOne',
                u'interface': u'internal'
            }, {
                u'url':
                u'http://admin:8774/v2/225da22d3ce34b15877ea70b2a575f58',
                u'region': u'RegionOne',
                u'interface': u'admin'
            }],
            u'type': u'compute'
        }, {
            u'endpoints': [{
                u'url': u'http://public.com:8773/services/Cloud',
                u'region': u'RegionOne',
                u'interface': u'public'
            }, {
                u'url': u'http://internal:8773/services/Cloud',
                u'region': u'RegionOne',
                u'interface': u'internal'
            }, {
                u'url': u'http://admin:8773/services/Admin',
                u'region': u'RegionOne',
                u'interface': u'admin'
            }],
            u'type': u'ec2'
        }, {
            u'endpoints': [{
                u'url': u'http://public.com:5000/v3',
                u'region': u'RegionOne',
                u'interface': u'public'
            }, {
                u'url': u'http://internal:5000/v3',
                u'region': u'RegionOne',
                u'interface': u'internal'
            }, {
                u'url': u'http://admin:35357/v3',
                u'region': u'RegionOne',
                u'interface': u'admin'
            }],
            u'type': u'identity'
        }],
        u'expires_at': u'2010-11-01T03:32:15-05:00',
        u'user': {
            u'domain': {
                u'id': u'4e6893b7ba0b4006840c3845660b86ed',
                u'name': u'exampledomain'
            },
            u'id': u'c4da488862bd435c9e6c0275a0d0e49a',
            u'name': u'exampleuser',
        },
        u'project': {
            u'domain': {
                u'id': u'4e6893b7ba0b4006840c3845660b86ed',
                u'name': u'exampledomain'
            },
            u'id': u'225da22d3ce34b15877ea70b2a575f58',
            u'name': u'exampleproject',
        },
    }
}

AUTH_RESPONSE_HEADERS = {
    u'X-Subject-Token': u'3e2813b7ba0b4006840c3825860b86ed'
}

AUTH_RESPONSE_BODY = {
    u'token': {
        u'methods': [
            u'password'
        ],
        u'expires_at': u'2010-11-01T03:32:15-05:00',
        u'project': {
            u'domain': {
                u'id': u'123',
                u'name': u'aDomain'
            },
            u'id': u'345',
            u'name': u'aTenant'
        },
        u'user': {
            u'domain': {
                u'id': u'1',
                u'name': u'aDomain'
            },
            u'id': u'567',
            u'name': u'test'
        },
        u'issued_at': u'2010-10-31T03:32:15-05:00',
        u'catalog': [{
            u'endpoints': [{
                u'url': u'https://compute.north.host/novapi/public',
                u'region': u'North',
                u'interface': u'public'
            }, {
                u'url': u'https://compute.north.host/novapi/internal',
                u'region': u'North',
                u'interface': u'internal'
            }, {
                u'url': u'https://compute.north.host/novapi/admin',
                u'region': u'North',
                u'interface': u'admin'
            }],
            u'type': u'compute'
        }, {
            u'endpoints': [{
                u'url': u'http://swift.north.host/swiftapi/public',
                u'region': u'South',
                u'interface': u'public'
            }, {
                u'url': u'http://swift.north.host/swiftapi/internal',
                u'region': u'South',
                u'interface': u'internal'
            }, {
                u'url': u'http://swift.north.host/swiftapi/admin',
                u'region': u'South',
                u'interface': u'admin'
            }],
            u'type': u'object-store'
        }, {
            u'endpoints': [{
                u'url': u'http://glance.north.host/glanceapi/public',
                u'region': u'North',
                u'interface': u'public'
            }, {
                u'url': u'http://glance.north.host/glanceapi/internal',
                u'region': u'North',
                u'interface': u'internal'
            }, {
                u'url': u'http://glance.north.host/glanceapi/admin',
                u'region': u'North',
                u'interface': u'admin'
            }, {
                u'url': u'http://glance.south.host/glanceapi/public',
                u'region': u'South',
                u'interface': u'public'
            }, {
                u'url': u'http://glance.south.host/glanceapi/internal',
                u'region': u'South',
                u'interface': u'internal'
            }, {
                u'url': u'http://glance.south.host/glanceapi/admin',
                u'region': u'South',
                u'interface': u'admin'
            }],
            u'type': u'image'
        }]
    }
}

TRUST_TOKEN = {
    u'token': {
        u'methods': [
            u'password'
        ],
        u'catalog': {},
        u'expires_at': u'2010-11-01T03:32:15-05:00',
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
        u'user': {
            u'domain': {
                u'id': u'4e6893b7ba0b4006840c3845660b86ed',
                u'name': u'exampledomain'
            },
            u'id': u'0ca8f6',
            u'name': u'exampleuser',
        }
    }
}
