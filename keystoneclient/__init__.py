# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
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

"""The python bindings for the OpenStack Identity (Keystone) project.

See :py:class:`keystoneclient.v3.client.Client` for the Identity V3 client.

See :py:class:`keystoneclient.v2_0.client.Client` for the Identity V2.0 client.

"""


import pbr.version

from keystoneclient import access
from keystoneclient import client
from keystoneclient import exceptions
from keystoneclient import generic
from keystoneclient import httpclient
from keystoneclient import service_catalog
from keystoneclient import v2_0
from keystoneclient import v3


__version__ = pbr.version.VersionInfo('python-keystoneclient').version_string()

__all__ = [
    # Modules
    'generic',
    'v2_0',
    'v3',

    # Packages
    'access',
    'client',
    'exceptions',
    'httpclient',
    'service_catalog',
]
