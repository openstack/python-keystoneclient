# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC
#
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

import unittest2 as unittest
from keystoneclient.contrib.ec2.utils import Ec2Signer


class Ec2SignerTest(unittest.TestCase):

    def setUp(self):
        super(Ec2SignerTest, self).setUp()
        self.access = '966afbde20b84200ae4e62e09acf46b2'
        self.secret = '89cdf9e94e2643cab35b8b8ac5a51f83'
        self.signer = Ec2Signer(self.secret)

    def tearDown(self):
        super(Ec2SignerTest, self).tearDown()

    def test_generate_0(self):
        """Test generate function for v0 signature"""
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': '0',
                                  'AWSAccessKeyId': self.access,
                                  'Timestamp': '2012-11-27T11:47:02Z',
                                  'Action': 'Foo'}}
        signature = self.signer.generate(credentials)
        expected = 'SmXQEZAUdQw5glv5mX8mmixBtas='
        self.assertEqual(signature, expected)

        pass

    def test_generate_1(self):
        """Test generate function for v1 signature"""
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': '1',
                                  'AWSAccessKeyId': self.access}}
        signature = self.signer.generate(credentials)
        expected = 'VRnoQH/EhVTTLhwRLfuL7jmFW9c='
        self.assertEqual(signature, expected)

    def test_generate_v2_SHA256(self):
        """Test generate function for v2 signature, SHA256"""
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': u'2',
                                  'AWSAccessKeyId': self.access}}
        signature = self.signer.generate(credentials)
        expected = 'odsGmT811GffUO0Eu13Pq+xTzKNIjJ6NhgZU74tYX/w='
        self.assertEqual(signature, expected)

    def test_generate_v2_SHA1(self):
        """Test generate function for v2 signature, SHA1"""
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': u'2',
                                  'AWSAccessKeyId': self.access}}
        self.signer.hmac_256 = None
        signature = self.signer.generate(credentials)
        expected = 'ZqCxMI4ZtTXWI175743mJ0hy/Gc='
        self.assertEqual(signature, expected)
