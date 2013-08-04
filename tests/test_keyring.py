import datetime

from keystoneclient import access
from keystoneclient import httpclient
from keystoneclient.openstack.common import timeutils

from tests import utils
from tests.v2_0 import client_fixtures

try:
    import keyring  # noqa
    import pickle  # noqa
except ImportError:
    keyring = None

PROJECT_SCOPED_TOKEN = client_fixtures.PROJECT_SCOPED_TOKEN

# These mirror values from PROJECT_SCOPED_TOKEN
USERNAME = 'exampleuser'
AUTH_URL = 'http://public.com:5000/v2.0'
TOKEN = '04c7d5ffaeef485f9dc69c06db285bdb'

PASSWORD = 'password'
TENANT = 'tenant'
TENANT_ID = 'tenant_id'


class KeyringTest(utils.TestCase):

    def setUp(self):
        if keyring is None:
            self.skipTest(
                'optional package keyring or pickle is not installed')

        class MemoryKeyring(keyring.backend.KeyringBackend):
            """Simple memory keyring with support for multiple keys."""
            def __init__(self):
                self.passwords = {}

            def supported(self):
                return 1

            def get_password(self, service, username):
                key = username + '@' + service
                if key not in self.passwords:
                    return None
                return self.passwords[key]

            def set_password(self, service, username, password):
                key = username + '@' + service
                self.passwords[key] = password

        super(KeyringTest, self).setUp()
        keyring.set_keyring(MemoryKeyring())

    def test_no_keyring_key(self):
        """Ensure that we get no value back if we don't have use_keyring
        set in the client.
        """
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL)

        (keyring_key, auth_ref) = cl.get_auth_ref_from_keyring(
            auth_url=AUTH_URL,
            username=USERNAME,
            tenant_name=TENANT,
            tenant_id=TENANT_ID,
            token=TOKEN)

        self.assertIsNone(keyring_key)
        self.assertIsNone(auth_ref)

    def test_build_keyring_key(self):
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL)

        keyring_key = cl._build_keyring_key(auth_url=AUTH_URL,
                                            username=USERNAME,
                                            tenant_name=TENANT,
                                            tenant_id=TENANT_ID,
                                            token=TOKEN)

        self.assertEqual(keyring_key,
                         '%s/%s/%s/%s/%s' %
                         (AUTH_URL, TENANT_ID, TENANT, TOKEN, USERNAME))

    def test_set_and_get_keyring_expired(self):
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL,
                                   use_keyring=True)
        keyring_key = cl._build_keyring_key(auth_url=AUTH_URL,
                                            username=USERNAME,
                                            tenant_name=TENANT,
                                            tenant_id=TENANT_ID,
                                            token=TOKEN)

        cl.auth_ref = access.AccessInfo.factory(body=PROJECT_SCOPED_TOKEN)
        expired = timeutils.utcnow() - datetime.timedelta(minutes=30)
        cl.auth_ref['token']['expires'] = timeutils.isotime(expired)
        cl.store_auth_ref_into_keyring(keyring_key)
        (keyring_key, auth_ref) = cl.get_auth_ref_from_keyring(
            auth_url=AUTH_URL,
            username=USERNAME,
            tenant_name=TENANT,
            tenant_id=TENANT_ID,
            token=TOKEN)
        self.assertIsNone(auth_ref)

    def test_set_and_get_keyring(self):
        cl = httpclient.HTTPClient(username=USERNAME, password=PASSWORD,
                                   tenant_id=TENANT_ID, auth_url=AUTH_URL,
                                   use_keyring=True)
        keyring_key = cl._build_keyring_key(auth_url=AUTH_URL,
                                            username=USERNAME,
                                            tenant_name=TENANT,
                                            tenant_id=TENANT_ID,
                                            token=TOKEN)

        cl.auth_ref = access.AccessInfo.factory(body=PROJECT_SCOPED_TOKEN)
        expires = timeutils.utcnow() + datetime.timedelta(minutes=30)
        cl.auth_ref['token']['expires'] = timeutils.isotime(expires)
        cl.store_auth_ref_into_keyring(keyring_key)
        (keyring_key, auth_ref) = cl.get_auth_ref_from_keyring(
            auth_url=AUTH_URL,
            username=USERNAME,
            tenant_name=TENANT,
            tenant_id=TENANT_ID,
            token=TOKEN)
        self.assertEqual(auth_ref.auth_token, TOKEN)
        self.assertEqual(auth_ref.username, USERNAME)
