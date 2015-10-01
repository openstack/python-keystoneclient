# Copyright 2013 OpenStack Foundation
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

"""Deprecated.

.. warning::

  This module is deprecated as of the 1.7.0 release in favor of
  :py:mod:`keystoneclient.exceptions` and may be removed in the 2.0.0 release.

"""

from debtcollector import removals

from keystoneclient import exceptions

# NOTE(akurilin): Module 'keystoneclient.apiclient' contains only exceptions
# which are deprecated, so this module must also be deprecated which helps
# to report 'deprecated' status of exceptions for next kind of imports
#       from keystoneclient.apiclient import exceptions

removals.removed_module('keystoneclient.apiclient',
                        replacement='keystoneclient.exceptions',
                        version='0.7.1',
                        removal_version='2.0')

__all__ = (
    'exceptions',
)
