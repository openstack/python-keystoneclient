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

from keystoneclient.common import cms
from keystoneclient import exceptions
from keystoneclient.tests import utils


class CMSTest(utils.TestCase):
    def test_cms_verify(self):
        self.assertRaises(exceptions.CertificateConfigError,
                          cms.cms_verify,
                          'data',
                          'no_exist_cert_file',
                          'no_exist_ca_file')
