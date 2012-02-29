# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 OpenStack LLC.
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

from keystoneclient import utils
from keystoneclient.generic import client

CLIENT_CLASS = client.Client


@utils.unauthenticated
def do_discover(cs, args):
    """
    Discover Keystone servers and show authentication protocols and
    extensions supported.

    Usage::
    $ keystone discover
    Keystone found at http://localhost:35357
        - supports version v1.0 (DEPRECATED) here http://localhost:35357/v1.0
        - supports version v1.1 (CURRENT) here http://localhost:35357/v1.1
        - supports version v2.0 (BETA) here http://localhost:35357/v2.0
            - and RAX-KSKEY: Rackspace API Key Authentication Admin Extension
            - and RAX-KSGRP: Rackspace Keystone Group Extensions
    """
    if cs.endpoint:
        versions = cs.discover(cs.endpoint)
    elif cs.auth_url:
        versions = cs.discover(cs.auth_url)
    else:
        versions = cs.discover()
    if versions:
        if 'message' in versions:
            print versions['message']
        for key, version in versions.iteritems():
            if key != 'message':
                print ("    - supports version %s (%s) here %s" %
                       (version['id'], version['status'], version['url']))
                extensions = cs.discover_extensions(version['url'])
                if extensions:
                    for key, extension in extensions.iteritems():
                        if key != 'message':
                            print ("        - and %s: %s" %
                                   (key, extension))
    else:
        print "No Keystone-compatible endpoint found"
