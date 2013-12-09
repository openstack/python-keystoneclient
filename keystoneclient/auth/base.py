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
import six


@six.add_metaclass(abc.ABCMeta)
class BaseAuthPlugin(object):
    """The basic structure of an authentication plugin."""

    @abc.abstractmethod
    def get_token(self, session, **kwargs):
        """Obtain a token.

        How the token is obtained is up to the plugin. If it is still valid
        it may be re-used, retrieved from cache or invoke an authentication
        request against a server.

        There are no required kwargs. They are passed directly to the auth
        plugin and they are implementation specific.

        Returning None will indicate that no token was able to be retrieved.

        :param session: A session object so the plugin can make HTTP calls.
        :return string: A token to use.
        """
