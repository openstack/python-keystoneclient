import testtools

from keystoneclient.middleware import memcache_crypt


class MemcacheCryptPositiveTests(testtools.TestCase):
    def test_generate_aes_key(self):
        self.assertEqual(
            len(memcache_crypt.generate_aes_key('Gimme Da Key', 'hush')), 32)

    def test_compute_mac(self):
        self.assertEqual(
            memcache_crypt.compute_mac('mykey', 'This is a test!'),
            'tREu41yR5tEgeBWIuv9ag4AeKA8=')

    def test_sign_data(self):
        expected = '{MAC:SHA1}eyJtYWMiOiAiM0FrQmdPZHRybGo1RFFESHA1eUxqcDVq' +\
                   'Si9BPSIsICJzZXJpYWxpemVkX2RhdGEiOiAiXCJUaGlzIGlzIGEgdG' +\
                   'VzdCFcIiJ9'
        self.assertEqual(
            memcache_crypt.sign_data('mykey', 'This is a test!'),
            expected)

    def test_verify_signed_data(self):
        signed = memcache_crypt.sign_data('mykey', 'Testz')
        self.assertEqual(
            memcache_crypt.verify_signed_data('mykey', signed),
            'Testz')
        self.assertEqual(
            memcache_crypt.verify_signed_data('aasSFWE13WER', 'not MACed'),
            'not MACed')

    def test_encrypt_data(self):
        expected = '{ENCRYPT:AES256}'
        self.assertEqual(
            memcache_crypt.encrypt_data('mykey', 'mysecret',
                                        'This is a test!')[:16],
            expected)

    def test_decrypt_data(self):
        encrypted = memcache_crypt.encrypt_data('mykey', 'mysecret', 'Testz')
        self.assertEqual(
            memcache_crypt.decrypt_data('mykey', 'mysecret', encrypted),
            'Testz')
        self.assertEqual(
            memcache_crypt.decrypt_data('mykey', 'mysecret',
                                        'Not Encrypted!'),
            'Not Encrypted!')

    def test_no_pycrypt(self):
        aes = memcache_crypt.AES
        memcache_crypt.AES = None
        self.assertRaises(memcache_crypt.CryptoUnavailableError,
                          memcache_crypt.encrypt_data, 'token', 'secret',
                          'data')
        memcache_crypt.AES = aes
