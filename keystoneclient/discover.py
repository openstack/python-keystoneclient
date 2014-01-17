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

import logging

import six

from keystoneclient import exceptions
from keystoneclient import httpclient
from keystoneclient.v2_0 import client as v2_client
from keystoneclient.v3 import client as v3_client


_logger = logging.getLogger(__name__)


class _KeystoneVersion(object):
    """A factory object that holds all the information to create a client.

     Instances of this class are callable objects that hold all the kwargs that
     were passed to discovery so that a user may simply call it to create a new
     client object.  Additional arguments passed to the call will override or
     add to those provided to the object.
    """

    _CLIENT_VERSIONS = {2: v2_client.Client,
                        3: v3_client.Client}

    def __init__(self, version, status, client_class=None, **kwargs):
        """Create a new discovered version object.

        :param tuple version: the version of the available API.
        :param string status: the stability of the API.
        :param Class client_class: the client class that should be used to
                                   instantiate against this version of the API.
                                   (optional, will be matched against known)
        :param dict **kwargs: Additional arguments that should be passed on to
                              the client when it is constructed.
        """
        self.version = version
        self.status = status
        self.client_class = client_class
        self.client_kwargs = kwargs

        if not self.client_class:
            try:
                self.client_class = self._CLIENT_VERSIONS[self.version[0]]
            except KeyError:
                raise exceptions.DiscoveryFailure("No client available "
                                                  "for version: %s" %
                                                  self.version)

    def __lt__(self, other):
        """Version Ordering.

        Versions are ordered by major, then minor version number, then
        'stable' is deemed the highest possible status, then they are just
        treated alphabetically (alpha < beta etc)
        """
        if self.version == other.version:
            if self.status == 'stable':
                return False
            elif other.status == 'stable':
                return True
            else:
                return self.status < other.status

        return self.version < other.version

    def __eq__(self, other):
        return self.version == other.version and self.status == other.status

    def __call__(self, **kwargs):
        if kwargs:
            client_kwargs = self.client_kwargs.copy()
            client_kwargs.update(kwargs)
        else:
            client_kwargs = self.client_kwargs
        return self.client_class(**client_kwargs)

    @property
    def _str_ver(self):
        ver = ".".join([str(v) for v in self.version])

        if self.status != 'stable':
            ver = "%s-%s" % (ver, self.status)

        return ver


def _normalize_version_number(version):
    """Turn a version representation into a tuple."""

    # trim the v from a 'v2.0' or similar
    try:
        version = version.lstrip('v')
    except AttributeError:
        pass

    # if it's an integer or a numeric as a string then normalize it
    # to a string, this ensures 1 decimal point
    try:
        num = float(version)
    except Exception:
        pass
    else:
        version = str(num)

    # if it's a string (or an integer) from above break it on .
    try:
        return tuple(map(int, version.split(".")))
    except Exception:
        pass

    # last attempt, maybe it's a list or iterable.
    try:
        return tuple(map(int, version))
    except Exception:
        pass

    raise TypeError("Invalid version specified: %s" % version)


def available_versions(url, **kwargs):
    headers = {'Accept': 'application/json'}

    client = httpclient.HTTPClient(**kwargs)
    resp, body_resp = client.request(url, 'GET', headers=headers)

    # In the event of querying a root URL we will get back a list of
    # available versions.
    try:
        return body_resp['versions']['values']
    except (KeyError, TypeError):
        pass

    # Otherwise if we query an endpoint like /v2.0 then we will get back
    # just the one available version.
    try:
        return [body_resp['version']]
    except (KeyError, TypeError):
        pass

    raise exceptions.DiscoveryFailure("Invalid Response - Bad version"
                                      " data returned: %s" % body_resp)


class Discover(object):
    """A means to discover and create clients depending on the supported API
    versions on the server.

    Querying the server is done on object creation and every subsequent method
    operates upon the data that was retrieved.
    """

    def __init__(self, **kwargs):
        """Construct a new discovery object.

        The connection parameters associated with this method are the same
        format and name as those used by a client (see
        keystoneclient.v2_0.client.Client and keystoneclient.v3.client.Client).
        If not overridden in subsequent methods they will also be what is
        passed to the constructed client.

        In the event that auth_url and endpoint is provided then auth_url will
        be used in accordance with how the client operates.

        The initialization process also queries the server.

        :param string auth_url: Identity service endpoint for authorization.
                                (optional)
        :param string endpoint: A user-supplied endpoint URL for the identity
                                service. (optional)
        :param string original_ip: The original IP of the requesting user
                                   which will be sent to identity service in a
                                   'Forwarded' header. (optional)
        :param boolean debug: Enables debug logging of all request and
                              responses to the identity service.
                              default False (optional)
        :param string cacert: Path to the Privacy Enhanced Mail (PEM) file
                              which contains the trusted authority X.509
                              certificates needed to established SSL connection
                              with the identity service. (optional)
        :param string key: Path to the Privacy Enhanced Mail (PEM) file which
                           contains the unencrypted client private key needed
                           to established two-way SSL connection with the
                           identity service. (optional)
        :param string cert: Path to the Privacy Enhanced Mail (PEM) file which
                            contains the corresponding X.509 client certificate
                            needed to established two-way SSL connection with
                            the identity service. (optional)
        :param boolean insecure: Does not perform X.509 certificate validation
                                 when establishing SSL connection with identity
                                 service. default: False (optional)
        """

        url = kwargs.get('endpoint') or kwargs.get('auth_url')
        if not url:
            raise exceptions.DiscoveryFailure('Not enough information to '
                                              'determine URL. Provide either '
                                              'auth_url or endpoint')

        self._client_kwargs = kwargs
        self._available_versions = available_versions(url, **kwargs)

    def _get_client_constructor_kwargs(self, kwargs_dict={}, **kwargs):
        client_kwargs = self._client_kwargs.copy()

        client_kwargs.update(kwargs_dict)
        client_kwargs.update(**kwargs)

        return client_kwargs

    def available_versions(self, unstable=False):
        """Return a list of identity APIs available on the server and the data
        associated with them.

        :param bool unstable: Accept endpoints not marked 'stable'. (optional)

        :returns: A List of dictionaries as presented by the server. Each dict
                  will contain the version and the URL to use for the version.
                  It is a direct representation of the layout presented by the
                  identity API.

        Example::

            >>> from keystoneclient import discover
            >>> disc = discover.Discovery(auth_url='http://localhost:5000')
            >>> disc.available_versions()
                [{'id': 'v3.0',
                    'links': [{'href': u'http://127.0.0.1:5000/v3/',
                               'rel': u'self'}],
                  'media-types': [
                      {'base': 'application/json',
                       'type': 'application/vnd.openstack.identity-v3+json'},
                      {'base': 'application/xml',
                       'type': 'application/vnd.openstack.identity-v3+xml'}],
                  'status': 'stable',
                  'updated': '2013-03-06T00:00:00Z'},
                 {'id': 'v2.0',
                  'links': [{'href': u'http://127.0.0.1:5000/v2.0/',
                             'rel': u'self'},
                            {'href': u'...',
                             'rel': u'describedby',
                             'type': u'application/pdf'}],
                  'media-types': [
                      {'base': 'application/json',
                       'type': 'application/vnd.openstack.identity-v2.0+json'},
                      {'base': 'application/xml',
                       'type': 'application/vnd.openstack.identity-v2.0+xml'}],
                  'status': 'stable',
                  'updated': '2013-03-06T00:00:00Z'}]
        """
        if unstable:
            # no need to determine the stable endpoints, just return everything
            return self._available_versions

        versions = []

        for v in self._available_versions:
            try:
                status = v['status']
            except KeyError:
                _logger.warning("Skipping over invalid version data. "
                                "No stability status in version.")
            else:
                if status == 'stable':
                    versions.append(v)

        return versions

    def _get_factory_from_response_entry(self, version_data, **kwargs):
        """Create a _KeystoneVersion factory object from a version response
        entry returned from a server.
        """
        try:
            version_str = version_data['id']
            status = version_data['status']

            if not version_str.startswith('v'):
                raise exceptions.DiscoveryFailure('Skipping over invalid '
                                                  'version string: %s. It '
                                                  'should start with a v.' %
                                                  version_str)

            for link in version_data['links']:
                # NOTE(jamielennox): there are plenty of links like with
                # documentation and such, we only care about the self
                # which is a link to the URL we should use.
                if link['rel'].lower() == 'self':
                    version_number = _normalize_version_number(version_str)
                    version_url = link['href']
                    break
            else:
                raise exceptions.DiscoveryFailure("Didn't find any links "
                                                  "in version data.")

        except (KeyError, TypeError, ValueError):
            raise exceptions.DiscoveryFailure('Skipping over invalid '
                                              'version data.')

        # NOTE(jamielennox): the url might be the auth_url or the endpoint
        # depending on what was passed initially. Order is important, endpoint
        # needs to override auth_url.
        for url_type in ('auth_url', 'endpoint'):
            if self._client_kwargs.get(url_type, False):
                kwargs[url_type] = version_url
            else:
                kwargs[url_type] = None

        return _KeystoneVersion(status=status,
                                version=version_number,
                                **kwargs)

    def _available_clients(self, unstable=False, **kwargs):
        """Return a dictionary of factory functions for available API versions.

        :returns: A dictionary of available API endpoints with the version
                  number as a tuple as the key, and a factory object that can
                  be used to create an appropriate client as the value.

        To use the returned factory you simply call it with the parameters to
        pass to keystoneclient. These parameters will override those saved in
        the factory.

        Example::

            >>> from keystoneclient import client
            >>> available_clients = client._available_clients(auth_url=url,
            ...                                               **kwargs)
            >>> try:
            ...     v2_factory = available_clients[(2, 0)]
            ... except KeyError:
            ...     print "Version 2.0 unavailable"
            ... else:
            ...     v2_client = v2_factory(token='abcdef')
            ...     v2_client.tenants.list()

        :raises: DiscoveryFailure if the response is invalid
        :raises: VersionNotAvailable if a suitable client cannot be found.
        """

        versions = dict()
        response_values = self.available_versions(unstable=unstable)
        client_kwargs = self._get_client_constructor_kwargs(kwargs_dict=kwargs)

        for version_data in response_values:
            try:
                v = self._get_factory_from_response_entry(version_data,
                                                          **client_kwargs)
            except exceptions.DiscoveryFailure as e:
                _logger.warning("Invalid entry: %s", e, exc_info=True)
            else:
                versions[v.version] = v

        return versions

    def create_client(self, version=None, **kwargs):
        """Factory function to create a new identity service client.

        :param tuple version: The required version of the identity API. If
                              specified the client will be selected such that
                              the major version is equivalent and an endpoint
                              provides at least the specified minor version.
                              For example to specify the 3.1 API use (3, 1).
                              (optional)
        :param bool unstable: Accept endpoints not marked 'stable'. (optional)
        :param kwargs: Additional arguments will override those provided to
                       this object's constructor.

        :returns: An instantiated identity client object.

        :raises: DiscoveryFailure if the server response is invalid
        :raises: VersionNotAvailable if a suitable client cannot be found.
        """
        versions = self._available_clients(**kwargs)
        chosen = None

        if version:
            version = _normalize_version_number(version)

            for keystone_version in six.itervalues(versions):
                # major versions must be the same (eg even though v2 is a lower
                # version than v3 we can't use it if v2 was requested)
                if version[0] != keystone_version.version[0]:
                    continue

                # prevent selecting a minor version less than what is required
                if version <= keystone_version.version:
                    chosen = keystone_version
                    break

        elif versions:
            # if no version specified pick the latest one
            chosen = max(six.iteritems(versions))[1]

        if not chosen:
            msg = "Could not find a suitable endpoint"

            if version:
                msg = "%s for client version: %s" % (msg, version)

            if versions:
                available = ", ".join([v._str_ver
                                       for v in six.itervalues(versions)])
                msg = "%s. Available_versions are: %s" % (msg, available)
            else:
                msg = "%s. No versions reported available" % msg

            raise exceptions.VersionNotAvailable(msg)

        return chosen()
