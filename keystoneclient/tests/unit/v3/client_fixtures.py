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
import uuid

from keystoneauth1 import fixture


def unscoped_token(**kwargs):
    return fixture.V3Token(**kwargs)


def domain_scoped_token(**kwargs):
    kwargs.setdefault('audit_chain_id', uuid.uuid4().hex)
    f = fixture.V3Token(**kwargs)
    if not f.domain_id:
        f.set_domain_scope()

    f.add_role(name='admin')
    f.add_role(name='member')
    region = 'RegionOne'

    s = f.add_service('volume')
    s.add_standard_endpoints(public='http://public.com:8776/v1/None',
                             internal='http://internal.com:8776/v1/None',
                             admin='http://admin.com:8776/v1/None',
                             region=region)

    s = f.add_service('image')
    s.add_standard_endpoints(public='http://public.com:9292/v1',
                             internal='http://internal:9292/v1',
                             admin='http://admin:9292/v1',
                             region=region)

    s = f.add_service('compute')
    s.add_standard_endpoints(public='http://public.com:8774/v1.1/None',
                             internal='http://internal:8774/v1.1/None',
                             admin='http://admin:8774/v1.1/None',
                             region=region)

    s = f.add_service('ec2')
    s.add_standard_endpoints(public='http://public.com:8773/services/Cloud',
                             internal='http://internal:8773/services/Cloud',
                             admin='http://admin:8773/services/Admin',
                             region=region)

    s = f.add_service('identity')
    s.add_standard_endpoints(public='http://public.com:5000/v3',
                             internal='http://internal:5000/v3',
                             admin='http://admin:35357/v3',
                             region=region)

    return f


def project_scoped_token(**kwargs):
    kwargs.setdefault('audit_chain_id', uuid.uuid4().hex)
    f = fixture.V3Token(**kwargs)

    if not f.project_id:
        f.set_project_scope()

    f.add_role(name='admin')
    f.add_role(name='member')

    region = 'RegionOne'
    tenant = '225da22d3ce34b15877ea70b2a575f58'

    s = f.add_service('volume')
    s.add_standard_endpoints(public='http://public.com:8776/v1/%s' % tenant,
                             internal='http://internal:8776/v1/%s' % tenant,
                             admin='http://admin:8776/v1/%s' % tenant,
                             region=region)

    s = f.add_service('image')
    s.add_standard_endpoints(public='http://public.com:9292/v1',
                             internal='http://internal:9292/v1',
                             admin='http://admin:9292/v1',
                             region=region)

    s = f.add_service('compute')
    s.add_standard_endpoints(public='http://public.com:8774/v2/%s' % tenant,
                             internal='http://internal:8774/v2/%s' % tenant,
                             admin='http://admin:8774/v2/%s' % tenant,
                             region=region)

    s = f.add_service('ec2')
    s.add_standard_endpoints(public='http://public.com:8773/services/Cloud',
                             internal='http://internal:8773/services/Cloud',
                             admin='http://admin:8773/services/Admin',
                             region=region)

    s = f.add_service('identity')
    s.add_standard_endpoints(public='http://public.com:5000/v3',
                             internal='http://internal:5000/v3',
                             admin='http://admin:35357/v3',
                             region=region)

    return f


AUTH_SUBJECT_TOKEN = uuid.uuid4().hex

AUTH_RESPONSE_HEADERS = {
    'X-Subject-Token': AUTH_SUBJECT_TOKEN,
}


def auth_response_body():
    f = fixture.V3Token(audit_chain_id=uuid.uuid4().hex)
    f.set_project_scope()

    f.add_role(name='admin')
    f.add_role(name='member')

    s = f.add_service('compute', name='nova')
    s.add_standard_endpoints(
        public='https://compute.north.host/novapi/public',
        internal='https://compute.north.host/novapi/internal',
        admin='https://compute.north.host/novapi/admin',
        region='North')

    s = f.add_service('object-store', name='swift')
    s.add_standard_endpoints(
        public='http://swift.north.host/swiftapi/public',
        internal='http://swift.north.host/swiftapi/internal',
        admin='http://swift.north.host/swiftapi/admin',
        region='South')

    s = f.add_service('image', name='glance')
    s.add_standard_endpoints(
        public='http://glance.north.host/glanceapi/public',
        internal='http://glance.north.host/glanceapi/internal',
        admin='http://glance.north.host/glanceapi/admin',
        region='North')

    s.add_standard_endpoints(
        public='http://glance.south.host/glanceapi/public',
        internal='http://glance.south.host/glanceapi/internal',
        admin='http://glance.south.host/glanceapi/admin',
        region='South')

    return f


def trust_token():
    f = fixture.V3Token(audit_chain_id=uuid.uuid4().hex)
    f.set_trust_scope()
    return f
