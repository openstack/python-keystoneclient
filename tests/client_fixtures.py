UNSCOPED_TOKEN = {
    u'access': {u'serviceCatalog': {},
                u'token': {u'expires': u'2012-10-03T16:58:01Z',
                           u'id': u'3e2813b7ba0b4006840c3825860b86ed'},
                u'user': {u'id': u'c4da488862bd435c9e6c0275a0d0e49a',
                          u'name': u'exampleuser',
                          u'roles': [],
                          u'roles_links': [],
                          u'username': u'exampleuser'}
                }
}

PROJECT_SCOPED_TOKEN = {
    u'access': {
        u'serviceCatalog': [{
            u'endpoints': [{
    u'adminURL': u'http://admin:8776/v1/225da22d3ce34b15877ea70b2a575f58',
    u'internalURL':
    u'http://internal:8776/v1/225da22d3ce34b15877ea70b2a575f58',
    u'publicURL':
    u'http://public.com:8776/v1/225da22d3ce34b15877ea70b2a575f58',
    u'region': u'RegionOne'
            }],
            u'endpoints_links': [],
            u'name': u'Volume Service',
            u'type': u'volume'},
            {u'endpoints': [{
    u'adminURL': u'http://admin:9292/v1',
    u'internalURL': u'http://internal:9292/v1',
    u'publicURL': u'http://public.com:9292/v1',
    u'region': u'RegionOne'}],
                u'endpoints_links': [],
                u'name': u'Image Service',
                u'type': u'image'},
            {u'endpoints': [{
u'adminURL': u'http://admin:8774/v2/225da22d3ce34b15877ea70b2a575f58',
u'internalURL': u'http://internal:8774/v2/225da22d3ce34b15877ea70b2a575f58',
u'publicURL': u'http://public.com:8774/v2/225da22d3ce34b15877ea70b2a575f58',
u'region': u'RegionOne'}],
                u'endpoints_links': [],
                u'name': u'Compute Service',
                u'type': u'compute'},
            {u'endpoints': [{
u'adminURL': u'http://admin:8773/services/Admin',
u'internalURL': u'http://internal:8773/services/Cloud',
u'publicURL': u'http://public.com:8773/services/Cloud',
u'region': u'RegionOne'}],
                u'endpoints_links': [],
                u'name': u'EC2 Service',
                u'type': u'ec2'},
            {u'endpoints': [{
u'adminURL': u'http://admin:35357/v2.0',
u'internalURL': u'http://internal:5000/v2.0',
u'publicURL': u'http://public.com:5000/v2.0',
u'region': u'RegionOne'}],
                u'endpoints_links': [],
                u'name': u'Identity Service',
                u'type': u'identity'}],
        u'token': {u'expires': u'2012-10-03T16:53:36Z',
                   u'id': u'04c7d5ffaeef485f9dc69c06db285bdb',
                   u'tenant': {u'description': u'',
                               u'enabled': True,
                               u'id': u'225da22d3ce34b15877ea70b2a575f58',
                               u'name': u'exampleproject'}},
        u'user': {u'id': u'c4da488862bd435c9e6c0275a0d0e49a',
                  u'name': u'exampleuser',
                  u'roles': [{u'id': u'edc12489faa74ee0aca0b8a0b4d74a74',
                              u'name': u'Member'}],
                  u'roles_links': [],
                  u'username': u'exampleuser'}
    }
}
