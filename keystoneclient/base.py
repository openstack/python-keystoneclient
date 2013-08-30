# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC
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

"""
Base utilities to build API operation managers and objects on top of.
"""

import abc
import functools
import urllib

import six

from keystoneclient import exceptions
from keystoneclient.openstack.common import strutils


def getid(obj):
    """Return id if argument is a Resource.

    Abstracts the common pattern of allowing both an object or an object's ID
    (UUID) as a parameter when dealing with relationships.
    """
    try:
        if obj.uuid:
            return obj.uuid
    except AttributeError:
        pass
    try:
        return obj.id
    except AttributeError:
        return obj


def filter_kwargs(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        for key, ref in kwargs.items():
            if ref is None:
                # drop null values
                del kwargs[key]
                continue

            id_value = getid(ref)
            if id_value == ref:
                continue

            # if an object with an id was passed remove the object
            # from params and replace it with just the id.
            # e.g user: User(id=1) becomes user_id: 1
            del kwargs[key]
            kwargs['%s_id' % key] = id_value

        return f(*args, **kwargs)
    return func


class Manager(object):
    """Basic manager type providing common operations.

    Managers interact with a particular type of API (servers, flavors, images,
    etc.) and provide CRUD operations for them.
    """
    resource_class = None

    def __init__(self, client):
        """Initializes Manager with `client`.

        :param client: instance of BaseClient descendant for HTTP requests
        """
        super(Manager, self).__init__()
        self.client = client

    @property
    def api(self):
        """Deprecated. Use `client` instead.
        """
        return self.client

    def _list(self, url, response_key, obj_class=None, body=None):
        """List the collection.

        :param url: a partial URL, e.g., '/servers'
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'servers'
        :param obj_class: class for constructing the returned objects
            (self.resource_class will be used by default)
        :param body: data that will be encoded as JSON and passed in POST
            request (GET will be sent by default)
        """
        if body:
            resp, body = self.client.post(url, body=body)
        else:
            resp, body = self.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        # NOTE(ja): keystone returns values as list as {'values': [ ... ]}
        #           unlike other services which just return the list...
        try:
            data = data['values']
        except (KeyError, TypeError):
            pass

        return [obj_class(self, res, loaded=True) for res in data if res]

    def _get(self, url, response_key):
        """Get an object from collection.

        :param url: a partial URL, e.g., '/servers'
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'server'
        """
        resp, body = self.client.get(url)
        return self.resource_class(self, body[response_key], loaded=True)

    def _head(self, url):
        """Retrieve request headers for an object.

        :param url: a partial URL, e.g., '/servers'
        """
        resp, body = self.client.head(url)
        return resp.status_code == 204

    def _create(self, url, body, response_key, return_raw=False):
        """Deprecated. Use `_post` instead.
        """
        return self._post(url, body, response_key, return_raw)

    def _post(self, url, body, response_key, return_raw=False):
        """Create an object.

        :param url: a partial URL, e.g., '/servers'
        :param body: data that will be encoded as JSON and passed in POST
            request (GET will be sent by default)
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'servers'
        :param return_raw: flag to force returning raw JSON instead of
            Python object of self.resource_class
        """
        resp, body = self.client.post(url, body=body)
        if return_raw:
            return body[response_key]
        return self.resource_class(self, body[response_key])

    def _put(self, url, body=None, response_key=None):
        """Update an object with PUT method.

        :param url: a partial URL, e.g., '/servers'
        :param body: data that will be encoded as JSON and passed in POST
            request (GET will be sent by default)
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'servers'
        """
        resp, body = self.client.put(url, body=body)
        # PUT requests may not return a body
        if body is not None:
            if response_key is not None:
                return self.resource_class(self, body[response_key])
            else:
                return self.resource_class(self, body)

    def _patch(self, url, body=None, response_key=None):
        """Update an object with PATCH method.

        :param url: a partial URL, e.g., '/servers'
        :param body: data that will be encoded as JSON and passed in POST
            request (GET will be sent by default)
        :param response_key: the key to be looked up in response dictionary,
            e.g., 'servers'
        """
        resp, body = self.client.patch(url, body=body)
        if response_key is not None:
            return self.resource_class(self, body[response_key])
        else:
            return self.resource_class(self, body)

    def _delete(self, url):
        """Delete an object.

        :param url: a partial URL, e.g., '/servers/my-server'
        """
        return self.client.delete(url)

    def _update(self, url, body=None, response_key=None, method="PUT",
                management=True):
        methods = {"PUT": self.client.put,
                   "POST": self.client.post,
                   "PATCH": self.client.patch}
        try:
            resp, body = methods[method](url, body=body,
                                         management=management)
        except KeyError:
            raise exceptions.ClientException("Invalid update method: %s"
                                             % method)
        # PUT requests may not return a body
        if body:
            return self.resource_class(self, body[response_key])


class ManagerWithFind(Manager):
    """Manager with additional `find()`/`findall()` methods."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def list(self):
        pass

    def find(self, **kwargs):
        """Find a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        rl = self.findall(**kwargs)
        num = len(rl)

        if num == 0:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise exceptions.NotFound(404, msg)
        elif num > 1:
            raise exceptions.NoUniqueMatch
        else:
            return rl[0]

    def findall(self, **kwargs):
        """Find all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        found = []
        searches = kwargs.items()

        for obj in self.list():
            try:
                if all(getattr(obj, attr) == value
                       for (attr, value) in searches):
                    found.append(obj)
            except AttributeError:
                continue

        return found


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
        """Builds a resource URL for the given kwargs.

        Given an example collection where `collection_key = 'entities'` and
        `key = 'entity'`, the following URL's could be generated.

        By default, the URL will represent a collection of entities, e.g.::

            /entities

        If kwargs contains an `entity_id`, then the URL will represent a
        specific member, e.g.::

            /entities/{entity_id}

        If a `base_url` is provided, the generated URL will be appended to it.

        """
        if dict_args_in_out is None:
            dict_args_in_out = {}

        url = dict_args_in_out.pop('base_url', None) or self.base_url or ''
        url += '/%s' % self.collection_key

        # do we have a specific entity?
        entity_id = dict_args_in_out.pop('%s_id' % self.key, None)
        if entity_id is not None:
            url += '/%s' % entity_id

        return url

    @filter_kwargs
    def create(self, **kwargs):
        url = self.build_url(dict_args_in_out=kwargs)
        return self._create(
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

    @filter_kwargs
    def list(self, **kwargs):
        url = self.build_url(dict_args_in_out=kwargs)

        return self._list(
            '%(url)s%(query)s' % {
                'url': url,
                'query': '?%s' % urllib.urlencode(kwargs) if kwargs else '',
            },
            self.collection_key)

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

        rl = self._list(
            '%(url)s%(query)s' % {
                'url': url,
                'query': '?%s' % urllib.urlencode(kwargs) if kwargs else '',
            },
            self.collection_key)
        num = len(rl)

        if num == 0:
            msg = "No %s matching %s." % (self.resource_class.__name__, kwargs)
            raise exceptions.NotFound(404, msg)
        elif num > 1:
            raise exceptions.NoUniqueMatch
        else:
            return rl[0]


class Resource(object):
    """Base class for OpenStack resources (tenant, user, etc.).

    This is pretty much just a bag for attributes.
    """

    HUMAN_ID = False
    NAME_ATTR = 'name'

    def __init__(self, manager, info, loaded=False):
        """Populate and bind to a manager.

        :param manager: Manager object
        :param info: dictionary representing resource attributes
        :param loaded: prevent lazy-loading if set to True
        """
        self.manager = manager
        self._info = {}
        self._add_details(info)
        self._loaded = loaded

    @property
    def human_id(self):
        """Human-readable ID which can be used for bash completion.
        """
        if self.NAME_ATTR in self.__dict__ and self.HUMAN_ID:
            return strutils.to_slug(getattr(self, self.NAME_ATTR))
        return None

    def _add_details(self, info):
        for (k, v) in six.iteritems(info):
            setattr(self, k, v)
            self._info[k] = v

    def __getattr__(self, k):
        if k not in self.__dict__:
            #NOTE(bcwaldon): disallow lazy-loading if already loaded once
            if not self.is_loaded():
                self.get()
                return self.__getattr__(k)

            raise AttributeError(k)
        else:
            return self.__dict__[k]

    def __repr__(self):
        reprkeys = sorted(k for k in self.__dict__.keys() if k[0] != '_' and
                          k != 'manager')
        info = ", ".join("%s=%s" % (k, getattr(self, k)) for k in reprkeys)
        return "<%s %s>" % (self.__class__.__name__, info)

    def get(self):
        # set_loaded() first ... so if we have to bail, we know we tried.
        self.set_loaded(True)
        if not hasattr(self.manager, 'get'):
            return

        new = self.manager.get(self.id)
        if new:
            self._add_details(new._info)

    def delete(self):
        return self.manager.delete(self)

    def __eq__(self, other):
        if not isinstance(other, Resource):
            return NotImplemented
        # two resources of different types are not equal
        if not isinstance(other, self.__class__):
            return False
        if hasattr(self, 'id') and hasattr(other, 'id'):
            return self.id == other.id
        return self._info == other._info

    def is_loaded(self):
        return self._loaded

    def set_loaded(self, val):
        self._loaded = val
