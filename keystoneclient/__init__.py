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

A Client object will allow you to communicate with the Identity server. The
recommended way to get a Client object is to use
:py:func:`keystoneclient.client.Client()`. :py:func:`~.Client()` uses version
discovery to create a V3 or V2 client depending on what versions the Identity
server supports and what version is requested.

Identity V2 and V3 clients can also be created directly. See
:py:class:`keystoneclient.v3.client.Client` for the V3 client and
:py:class:`keystoneclient.v2_0.client.Client` for the V2 client.

"""

import importlib
import sys

import pbr.version


__version__ = pbr.version.VersionInfo('python-keystoneclient').version_string()

__all__ = (
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
)


class _LazyImporter(object):
    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        # NB: this is only called until the import has been done.
        # These submodules are part of the API without explicit importing, but
        # expensive to load, so we load them on-demand rather than up-front.
        lazy_submodules = [
            'access',
            'client',
            'exceptions',
            'generic',
            'httpclient',
            'service_catalog',
            'v2_0',
            'v3',
        ]
        if name in lazy_submodules:
            return importlib.import_module('keystoneclient.%s' % name)

        # Return module attributes like __all__ etc.
        return getattr(self._module, name)


sys.modules[__name__] = _LazyImporter(sys.modules[__name__])
