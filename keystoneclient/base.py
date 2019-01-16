# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack Foundation
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

"""Base utilities to build API operation managers and objects on top of."""

import abc
import copy
import functools
import warnings

from keystoneauth1 import exceptions as ksa_exceptions
from keystoneauth1 import plugin
from oslo_utils import strutils
import six
from six.moves import urllib

from keystoneclient import exceptions as ksc_exceptions
from keystoneclient.i18n import _


class Response(object):

    def __init__(self, http_response, data):
        self.request_ids = []
        if isinstance(http_response, list):
            # http_response is a list of <requests.Response> in case
            # of pagination
            for resp_obj in http_response:
                # Extract 'x-openstack-request-id' from headers
                self.request_ids.append(resp_obj.headers.get(
                    'x-openstack-request-id'))
        else:
            self.request_ids.append(http_response.headers.get(
                'x-openstack-request-id'))
        self.data = data


def getid(obj):
    """Return id if argument is a Resource.

    Abstracts the common pattern of allowing both an object or an object's ID
    (UUID) as a parameter when dealing with relationships.
    """
    if getattr(obj, 'uuid', None):
        return obj.uuid
    else:
        return getattr(obj, 'id', obj)


def filter_none(**kwargs):
    """Remove any entries from a dictionary where the value is None."""
    return dict((k, v) for k, v in kwargs.items() if v is not None)


def filter_kwargs(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        new_kwargs = {}
        for key, ref in kwargs.items():
            if ref is None:
                # drop null values
                continue

            id_value = getid(ref)
            if id_value != ref:
                # If an object with an id was passed, then use the id, e.g.:
                #     user: user(id=1) becomes user_id: 1
                key = '%s_id' % key

            new_kwargs[key] = id_value

        return f(*args, **new_kwargs)
    return func


class Manager(object):
    """Basic manager type providing common operations.

    Managers interact with a particular type of API (servers, flavors, images,
    etc.) and provide CRUD operations for them.

    :param client: instance of BaseClient descendant for HTTP requests

    """

    resource_class = None

    def __init__(self, client):
        super(Manager, self).__init__()
        self.client = client

    @property
    def api(self):
        """The client.

        .. warning::

            This property is deprecated as of the 1.7.0 release in favor of
            :meth:`client` and may be removed in the 2.0.0 release.

        """
        warnings.warn(
            'api is deprecated as of the 1.7.0 release in favor of client and '
            'may be removed in the 2.0.0 release', DeprecationWarning)
        return self.client

    def _prepare_return_value(self, http_response, data):
        if self.client.include_metadata:
            return Response(http_response, data)
        return data

    def _list(self, url, response_key, obj_class=None, body=None, **kwargs):
        """List the collection.

        :param url: a partial URL, e.g., '/servers'
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'servers'
        :param obj_class: class for constructing the returned objects
            (self.resource_class will be used by default)
        :param body: data that will be encoded as JSON and passed in POST
            request (GET will be sent by default)
        :param kwargs: Additional arguments will be passed to the request.
        """
        if body:
            resp, body = self.client.post(url, body=body, **kwargs)
        else:
            resp, body = self.client.get(url, **kwargs)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        # NOTE(ja): keystone returns values as list as {'values': [ ... ]}
        #           unlike other services which just return the list...
        try:
            data = data['values']
        except (KeyError, TypeError):  # nosec(cjschaef): keystone data values
            # not as expected (see comment above), assumption is that values
            # are already returned in a list (so simply utilize that list)
            pass

        return self._prepare_return_value(
            resp, [obj_class(self, res, loaded=True) for res in data if res])

    def _get(self, url, response_key, **kwargs):
        """Get an object from collection.

        :param url: a partial URL, e.g., '/servers'
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'server'
        :param kwargs: Additional arguments will be passed to the request.
        """
        resp, body = self.client.get(url, **kwargs)
        return self._prepare_return_value(
            resp, self.resource_class(self, body[response_key], loaded=True))

    def _head(self, url, **kwargs):
        """Retrieve request headers for an object.

        :param url: a partial URL, e.g., '/servers'
        :param kwargs: Additional arguments will be passed to the request.
        """
        resp, body = self.client.head(url, **kwargs)
        return self._prepare_return_value(resp, resp.status_code == 204)

    def _post(self, url, body, response_key, return_raw=False, **kwargs):
        """Create an object.

        :param url: a partial URL, e.g., '/servers'
        :param body: data that will be encoded as JSON and passed in POST
            request (GET will be sent by default)
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'servers'
        :param return_raw: flag to force returning raw JSON instead of
            Python object of self.resource_class
        :param kwargs: Additional arguments will be passed to the request.
        """
        resp, body = self.client.post(url, body=body, **kwargs)
        if return_raw:
            return body[response_key]
        return self._prepare_return_value(
            resp, self.resource_class(self, body[response_key]))

    def _put(self, url, body=None, response_key=None, **kwargs):
        """Update an object with PUT method.

        :param url: a partial URL, e.g., '/servers'
        :param body: data that will be encoded as JSON and passed in POST
            request (GET will be sent by default)
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'servers'
        :param kwargs: Additional arguments will be passed to the request.
        """
        resp, body = self.client.put(url, body=body, **kwargs)
        # PUT requests may not return a body
        if body is not None:
            if response_key is not None:
                return self._prepare_return_value(
                    resp, self.resource_class(self, body[response_key]))
            else:
                return self._prepare_return_value(
                    resp, self.resource_class(self, body))
        # In some cases (e.g. 'add_endpoint_to_project' from endpoint_filters
        # resource), PUT request may not return a body so return None as
        # response along with request_id if include_metadata is True.
        return self._prepare_return_value(resp, body)

    def _patch(self, url, body=None, response_key=None, **kwargs):
        """Update an object with PATCH method.

        :param url: a partial URL, e.g., '/servers'
        :param body: data that will be encoded as JSON and passed in POST
            request (GET will be sent by default)
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'servers'
        :param kwargs: Additional arguments will be passed to the request.
        """
        resp, body = self.client.patch(url, body=body, **kwargs)
        if response_key is not None:
            return self._prepare_return_value(
                resp, self.resource_class(self, body[response_key]))
        else:
            return self._prepare_return_value(
                resp, self.resource_class(self, body))

    def _delete(self, url, **kwargs):
        """Delete an object.

        :param url: a partial URL, e.g., '/servers/my-server'
        :param kwargs: Additional arguments will be passed to the request.
        """
        resp, body = self.client.delete(url, **kwargs)
        return resp, self._prepare_return_value(resp, body)

    def _update(self, url, body=None, response_key=None, method="PUT",
                **kwargs):
        methods = {"PUT": self.client.put,
                   "POST": self.client.post,
                   "PATCH": self.client.patch}
        try:
            resp, body = methods[method](url, body=body,
                                         **kwargs)
        except KeyError:
            raise ksc_exceptions.ClientException(_("Invalid update method: %s")
                                                 % method)
        # PUT requests may not return a body
        if body:
            return self._prepare_return_value(
                resp, self.resource_class(self, body[response_key]))
        else:
            return self._prepare_return_value(resp, body)


@six.add_metaclass(abc.ABCMeta)
class ManagerWithFind(Manager):
    """Manager with additional `find()`/`findall()` methods."""

    @abc.abstractmethod
    def list(self):
        pass  # pragma: no cover

    def find(self, **kwargs):
        """Find a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        rl = self.findall(**kwargs)

        if self.client.include_metadata:
            base_response = rl
            rl = rl.data
            base_response.data = rl[0]

        if len(rl) == 0:
            msg = _("No %(name)s matching %(kwargs)s.") % {
                'name': self.resource_class.__name__, 'kwargs': kwargs}
            raise ksa_exceptions.NotFound(404, msg)
        elif len(rl) > 1:
            raise ksc_exceptions.NoUniqueMatch
        else:
            return base_response if self.client.include_metadata else rl[0]

    def findall(self, **kwargs):
        """Find all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = kwargs.items()

        def _extract_data(objs, response_data):
            for obj in objs:
                try:
                    if all(getattr(obj, attr) == value
                           for (attr, value) in searches):
                        response_data.append(obj)
                except AttributeError:
                    continue
            return response_data

        objs = self.list()
        if self.client.include_metadata:
            # 'objs' is the object of 'Response' class.
            objs.data = _extract_data(objs.data, found)
            return objs

        return _extract_data(objs, found)


class CrudManager(Manager):
    """Base manager class for manipulating Keystone entities.

    Children of this class are expected to define a `collection_key` and `key`.

    - `collection_key`: Usually a plural noun by convention (e.g. `entities`);
      used to refer collections in both URL's (e.g.  `/v3/entities`) and JSON
      objects containing a list of member resources (e.g. `{'entities': [{},
      {}, {}]}`).
    - `key`: Usually a singular noun by convention (e.g. `entity`); used to
      refer to an individual member of the collection.

    """

    collection_key = None
    key = None
    base_url = None

    def build_url(self, dict_args_in_out=None):
        """Build a resource URL for the given kwargs.

        Given an example collection where `collection_key = 'entities'` and
        `key = 'entity'`, the following URL's could be generated.

        By default, the URL will represent a collection of entities, e.g.::

            /entities

        If kwargs contains an `entity_id`, then the URL will represent a
        specific member, e.g.::

            /entities/{entity_id}

        If a `base_url` is provided, the generated URL will be appended to it.

        If a 'tail' is provided, it will be appended to the end of the URL.

        """
        if dict_args_in_out is None:
            dict_args_in_out = {}

        url = dict_args_in_out.pop('base_url', None) or self.base_url or ''
        url += '/%s' % self.collection_key

        # do we have a specific entity?
        entity_id = dict_args_in_out.pop('%s_id' % self.key, None)
        if entity_id is not None:
            url += '/%s' % entity_id

        if dict_args_in_out.get('tail'):
            url += dict_args_in_out['tail']

        return url

    @filter_kwargs
    def create(self, **kwargs):
        url = self.build_url(dict_args_in_out=kwargs)
        return self._post(
            url,
            {self.key: kwargs},
            self.key)

    @filter_kwargs
    def get(self, **kwargs):
        return self._get(
            self.build_url(dict_args_in_out=kwargs),
            self.key)

    @filter_kwargs
    def head(self, **kwargs):
        return self._head(self.build_url(dict_args_in_out=kwargs))

    def _build_query(self, params):
        if params is None:
            return ''
        else:
            # NOTE(spilla) Since the manager cannot take in a hyphen as a
            # key in the kwarg, it is passed in with a _.  This needs to be
            # replaced with a proper hyphen for the URL to work properly.
            tags_params = ('tags_any', 'not_tags', 'not_tags_any')
            for tag_param in tags_params:
                if tag_param in params:
                    params[tag_param.replace('_', '-')] = params.pop(tag_param)
            return '?%s' % urllib.parse.urlencode(params, doseq=True)

    def build_key_only_query(self, params_list):
        """Build a query that does not include values, just keys.

        The Identity API has some calls that define queries without values,
        this can not be accomplished by using urllib.parse.urlencode(). This
        method builds a query using only the keys.
        """
        return '?%s' % '&'.join(params_list) if params_list else ''

    @filter_kwargs
    def list(self, fallback_to_auth=False, **kwargs):

        def return_resp(resp, include_metadata=False):
            base_response = None
            list_data = resp
            if include_metadata:
                base_response = resp
                list_data = resp.data
                base_response.data = list_data
            return base_response if include_metadata else list_data

        if 'id' in kwargs.keys():
            # Ensure that users are not trying to call things like
            # ``domains.list(id='default')`` when they should have used
            # ``[domains.get(domain_id='default')]`` instead. Keystone supports
            # ``GET /v3/domains/{domain_id}``, not ``GET
            # /v3/domains?id={domain_id}``.
            raise TypeError(
                _("list() got an unexpected keyword argument 'id'. To "
                  "retrieve a single object using a globally unique "
                  "identifier, try using get() instead."))

        url = self.build_url(dict_args_in_out=kwargs)

        try:
            query = self._build_query(kwargs)
            url_query = '%(url)s%(query)s' % {'url': url, 'query': query}
            list_resp = self._list(url_query, self.collection_key)
            return return_resp(list_resp,
                               include_metadata=self.client.include_metadata)
        except ksa_exceptions.EmptyCatalog:
            if fallback_to_auth:
                list_resp = self._list(url_query, self.collection_key,
                                       endpoint_filter={
                                           'interface': plugin.AUTH_INTERFACE})
                return return_resp(
                    list_resp, include_metadata=self.client.include_metadata)
            else:
                raise

    @filter_kwargs
    def put(self, **kwargs):
        return self._update(
            self.build_url(dict_args_in_out=kwargs),
            method='PUT')

    @filter_kwargs
    def update(self, **kwargs):
        url = self.build_url(dict_args_in_out=kwargs)

        return self._update(
            url,
            {self.key: kwargs},
            self.key,
            method='PATCH')

    @filter_kwargs
    def delete(self, **kwargs):
        return self._delete(
            self.build_url(dict_args_in_out=kwargs))

    @filter_kwargs
    def find(self, **kwargs):
        """Find a single item with attributes matching ``**kwargs``."""
        url = self.build_url(dict_args_in_out=kwargs)

        query = self._build_query(kwargs)
        url_query = '%(url)s%(query)s' % {
            'url': url,
            'query': query
        }
        elements = self._list(
            url_query,
            self.collection_key)

        if self.client.include_metadata:
            base_response = elements
            elements = elements.data
            base_response.data = elements[0]

        if not elements:
            msg = _("No %(name)s matching %(kwargs)s.") % {
                'name': self.resource_class.__name__, 'kwargs': kwargs}
            raise ksa_exceptions.NotFound(404, msg)
        elif len(elements) > 1:
            raise ksc_exceptions.NoUniqueMatch
        else:
            return (base_response if self.client.include_metadata
                    else elements[0])


class Resource(object):
    """Base class for OpenStack resources (tenant, user, etc.).

    This is pretty much just a bag for attributes.
    """

    HUMAN_ID = False
    NAME_ATTR = 'name'

    def __init__(self, manager, info, loaded=False):
        """Populate and bind to a manager.

        :param manager: BaseManager object
        :param info: dictionary representing resource attributes
        :param loaded: prevent lazy-loading if set to True
        """
        self.manager = manager
        self._info = info
        self._add_details(info)
        self._loaded = loaded

    def __repr__(self):
        """Return string representation of resource attributes."""
        reprkeys = sorted(k
                          for k in self.__dict__.keys()
                          if k[0] != '_' and k != 'manager')
        info = ", ".join("%s=%s" % (k, getattr(self, k)) for k in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)

    @property
    def human_id(self):
        """Human-readable ID which can be used for bash completion."""
        if self.HUMAN_ID:
            name = getattr(self, self.NAME_ATTR, None)
            if name is not None:
                return strutils.to_slug(name)
        return None

    def _add_details(self, info):
        for (k, v) in info.items():
            try:
                try:
                    setattr(self, k, v)
                except UnicodeEncodeError:
                    # This happens when we're running with Python version that
                    # does not support Unicode identifiers (e.g. Python 2.7).
                    # In that case we can't help but not set this attrubute;
                    # it'll be available in a dict representation though
                    pass
                self._info[k] = v
            except AttributeError:  # nosec(cjschaef): we already defined the
                # attribute on the class
                pass

    def __getattr__(self, k):
        """Checking attrbiute existence."""
        if k not in self.__dict__:
            # NOTE(bcwaldon): disallow lazy-loading if already loaded once
            if not self.is_loaded():
                self.get()
                return self.__getattr__(k)

            raise AttributeError(k)
        else:
            return self.__dict__[k]

    def get(self):
        """Support for lazy loading details.

        Some clients, such as novaclient have the option to lazy load the
        details, details which can be loaded with this function.
        """
        # set_loaded() first ... so if we have to bail, we know we tried.
        self.set_loaded(True)
        if not hasattr(self.manager, 'get'):
            return

        new = self.manager.get(self.id)
        if new:
            self._add_details(new._info)

    def __eq__(self, other):
        """Define equality for resources."""
        if not isinstance(other, Resource):
            return NotImplemented
        # two resources of different types are not equal
        if not isinstance(other, self.__class__):
            return False
        return self._info == other._info

    def __ne__(self, other):
        """Define inequality for resources."""
        return not self == other

    def is_loaded(self):
        return self._loaded

    def set_loaded(self, val):
        self._loaded = val

    def to_dict(self):
        return copy.deepcopy(self._info)

    def delete(self):
        return self.manager.delete(self)
