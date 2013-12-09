# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import abc
import logging
import six

from keystoneclient.auth import base

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseIdentityPlugin(base.BaseAuthPlugin):

    def __init__(self,
                 auth_url=None,
                 username=None,
                 password=None,
                 token=None,
                 trust_id=None):

        super(BaseIdentityPlugin, self).__init__()

        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.token = token
        self.trust_id = trust_id

        self.auth_ref = None

    @abc.abstractmethod
    def get_auth_ref(self, session, **kwargs):
        """Obtain a token from an OpenStack Identity Service.

        This method is overridden by the various token version plugins.

        This function should not be called independently and is expected to be
        invoked via the do_authenticate function.

        :returns AccessInfo: Token access information.
        """

    def get_token(self, session, **kwargs):
        if not self.auth_ref or self.auth_ref.will_expire_soon(1):
            self.auth_ref = self.get_auth_ref(session, **kwargs)

        return self.auth_ref.auth_token
