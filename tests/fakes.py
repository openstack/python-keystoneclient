"""
A fake server that "responds" to API methods with pre-canned responses.

All of these responses come from the spec, so if for some reason the spec's
wrong the tests might raise AssertionError. I've indicated in comments the
places where actual behavior differs from the spec.
"""

from keystoneclient import access


def assert_has_keys(dict, required=[], optional=[]):
    keys = dict.keys()
    for k in required:
        try:
            assert k in keys
        except AssertionError:
            extra_keys = set(keys).difference(set(required + optional))
            raise AssertionError("found unexpected keys: %s" %
                                 list(extra_keys))


class FakeClient(object):

    def assert_called(self, method, url, body=None, pos=-1):
        """Assert than an API method was just called."""
        expected = (method, url)
        called = self.callstack[pos][0:2]

        assert self.callstack, ("Expected %s %s but no calls were made." %
                                expected)
        assert expected == called, ("Expected %s %s; got %s %s" %
                                    (expected + called))

        if body is not None:
            assert self.callstack[pos][2] == body

    def assert_called_anytime(self, method, url, body=None):
        """Assert than an API method was called anytime in the test."""
        expected = (method, url)

        assert self.callstack, ("Expected %s %s but no calls were made." %
                                expected)

        found = False
        for entry in self.callstack:
            if expected == entry[0:2]:
                found = True
                break

        assert found, ('Expected %s; got %s' %
                       (expected, self.callstack))
        if body is not None:
            if entry[2] != body:
                raise AssertionError('%s != %s' % (entry[2], body))
        self.callstack = []

    def clear_callstack(self):
        self.callstack = []

    def authenticate(self, cl_obj):
        cl_obj.user_id = '1'
        cl_obj.auth_user_id = '1'
        cl_obj.project_id = '1'
        cl_obj.auth_tenant_id = '1'
        cl_obj.auth_ref = access.AccessInfo.factory(None, {
            "access": {
                "token": {
                    "expires": "2012-02-05T00:00:00",
                    "id": "887665443383838",
                    "tenant": {
                        "id": "1",
                        "name": "customer-x"
                    }
                },
                "serviceCatalog": [{
                    "endpoints": [{
                        "adminURL": "http://swift.admin-nets.local:8080/",
                        "region": "RegionOne",
                        "internalURL": "http://127.0.0.1:8080/v1/AUTH_1",
                        "publicURL":
                        "http://swift.publicinternets.com/v1/AUTH_1"
                    }],
                    "type": "object-store",
                    "name": "swift"
                }, {
                    "endpoints": [{
                        "adminURL": "http://cdn.admin-nets.local/v1.1/1",
                        "region": "RegionOne",
                        "internalURL": "http://127.0.0.1:7777/v1.1/1",
                        "publicURL": "http://cdn.publicinternets.com/v1.1/1"
                    }],
                    "type": "object-store",
                    "name": "cdn"
                }],
                "user": {
                    "id": "1",
                    "roles": [{
                        "tenantId": "1",
                        "id": "3",
                        "name": "Member"
                    }],
                    "name": "joeuser"
                }
            }
        })
