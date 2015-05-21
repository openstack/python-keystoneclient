#!/bin/bash -x

# Copyright 2012 OpenStack Foundation
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

# This script generates the crypto necessary for the SSL tests.

. gen_pki.sh

check_openssl
rm_old
cleanup
setup
generate_ca
ssl_cert_req
cms_signing_cert_req
issue_certs
create_middleware_cert
gen_sample_cms
cleanup
