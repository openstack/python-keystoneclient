======================
Authentication Plugins
======================

Introduction
============

Authentication plugins provide a generic means by which to extend the
authentication mechanisms known to OpenStack clients.

In the vast majority of cases the authentication plugins used will be those
written for use with the OpenStack Identity Service (Keystone), however this is
not the only possible case, and the mechanisms by which authentication plugins
are used and implemented should be generic enough to cover completely
customized authentication solutions.

The subset of authentication plugins intended for use with an OpenStack
Identity server (such as Keystone) are called Identity Plugins.


Available Plugins
=================

Keystoneclient ships with a number of plugins and particularly Identity
Plugins.

V2 Identity Plugins
-------------------

Standard V2 identity plugins are defined in the module:
:py:mod:`keystoneclient.auth.identity.v2`

They include:

- :py:class:`~keystoneclient.auth.identity.v2.Password`: Authenticate against
  a V2 identity service using a username and password.
- :py:class:`~keystoneclient.auth.identity.v2.Token`: Authenticate against a
  V2 identity service using an existing token.

V2 identity plugins must use an auth_url that points to the root of a V2
identity server URL, i.e.: `http://hostname:5000/v2.0`.

V3 Identity Plugins
-------------------

Standard V3 identity plugins are defined in the module
:py:mod:`keystoneclient.auth.identity.v3`.

V3 Identity plugins are slightly different from their V2 counterparts as a V3
authentication request can contain multiple authentication methods.  To handle
this V3 defines a number of different
:py:class:`~keystoneclient.auth.identity.v3.AuthMethod` classes:

- :py:class:`~keystoneclient.auth.identity.v3.PasswordMethod`: Authenticate
  against a V3 identity service using a username and password.
- :py:class:`~keystoneclient.auth.identity.v3.TokenMethod`: Authenticate against
  a V3 identity service using an existing token.

The :py:class:`~keystoneclient.auth.identity.v3.AuthMethod` objects are then
passed to the :py:class:`~keystoneclient.auth.identity.v3.Auth` plugin::

    >>> from keystoneclient import session
    >>> from keystoneclient.auth.identity import v3
    >>> password = v3.PasswordMethod(username='user',
    ...                              password='password')
    >>> auth = v3.Auth(auth_url='http://my.keystone.com:5000/v3',
    ...                auth_methods=[password],
    ...                project_id='projectid')
    >>> sess = session.Session(auth=auth)

As in the majority of cases you will only want to use one
:py:class:`~keystoneclient.auth.identity.v3.AuthMethod` there are also helper
authentication plugins for the various
:py:class:`~keystoneclient.auth.identity.v3.AuthMethod` which can be used more
like the V2 plugins:

- :py:class:`~keystoneclient.auth.identity.v3.Password`: Authenticate using
  only a :py:class:`~keystoneclient.auth.identity.v3.PasswordMethod`.
- :py:class:`~keystoneclient.auth.identity.v3.Token`: Authenticate using only a
  :py:class:`~keystoneclient.auth.identity.v3.TokenMethod`.

::

    >>> auth = v3.Password(auth_url='http://my.keystone.com:5000/v3',
    ...                    username='username',
    ...                    password='password',
    ...                    project_id='projectid')
    >>> sess = session.Session(auth=auth)

This will have exactly the same effect as using the single
:py:class:`~keystoneclient.auth.identity.v3.PasswordMethod` above.

V3 identity plugins must use an auth_url that points to the root of a V3
identity server URL, i.e.: `http://hostname:5000/v3`.

Version Independent Identity Plugins
------------------------------------

Standard version independent identity plugins are defined in the module
:py:mod:`keystoneclient.auth.identity.generic`.

For the cases of plugins that exist under both the identity V2 and V3 APIs
there is an abstraction to allow the plugin to determine which of the V2 and V3
APIs are supported by the server and use the most appropriate API.

These plugins are:

- :py:class:`~keystoneclient.auth.identity.generic.Password`: Authenticate
  using a user/password against either v2 or v3 API.
- :py:class:`~keystoneclient.auth.identity.generic.Token`: Authenticate using
  an existing token against either v2 or v3 API.

These plugins work by first querying the identity server to determine available
versions and so the `auth_url` used with the plugins should point to the base
URL of the identity server to use. If the `auth_url` points to either a V2 or
V3 endpoint it will restrict the plugin to only working with that version of
the API.

Simple Plugins
--------------

In addition to the Identity plugins a simple plugin that will always use the
same provided token and endpoint is available. This is useful in situations
where you have an ``ADMIN_TOKEN`` or in testing when you specifically know the
endpoint you want to communicate with.

It can be found at :py:class:`keystoneclient.auth.token_endpoint.Token`.


V3 OAuth 1.0a Plugins
---------------------

There also exists a plugin for OAuth 1.0a authentication. We provide a helper
authentication plugin at:
:py:class:`~keystoneclient.v3.contrib.oauth1.auth.OAuth`.
The plugin requires the OAuth consumer's key and secret, as well as the OAuth
access token's key and secret. For example::

    >>> from keystoneclient.v3.contrib.oauth1 import auth
    >>> from keystoneclient import session
    >>> from keystoneclient.v3 import client
    >>> a = auth.OAuth('http://my.keystone.com:5000/v3',
    ...                consumer_key=consumer_id,
    ...                consumer_secret=consumer_secret,
    ...                access_key=access_token_key,
    ...                access_secret=access_token_secret)
    >>> s = session.Session(auth=a)


Loading Plugins by Name
=======================

In auth_token middleware and for some service to service communication it is
possible to specify a plugin to load via name. The authentication options that
are available are then specific to the plugin that you specified. Currently the
authentication plugins that are available in `keystoneclient` are:

- password: :py:class:`keystoneclient.auth.identity.generic.Password`
- token: :py:class:`keystoneclient.auth.identity.generic.Token`
- v2password: :py:class:`keystoneclient.auth.identity.v2.Password`
- v2token: :py:class:`keystoneclient.auth.identity.v2.Token`
- v3password: :py:class:`keystoneclient.auth.identity.v3.Password`
- v3token: :py:class:`keystoneclient.auth.identity.v3.Token`


Creating Authentication Plugins
===============================

Creating an Identity Plugin
---------------------------

If you have implemented a new authentication mechanism into the Identity
service then you will be able to reuse a lot of the infrastructure available
for the existing Identity mechanisms. As the V2 identity API is essentially
frozen, it is expected that new plugins are for the V3 API.

To implement a new V3 plugin that can be combined with others you should
implement the base :py:class:`keystoneclient.auth.identity.v3.AuthMethod` class
and implement the
:py:meth:`~keystoneclient.auth.identity.v3.AuthMethod.get_auth_data` function.
If your Plugin cannot be used in conjunction with existing
:py:class:`keystoneclient.auth.identity.v3.AuthMethod` then you should just
override :py:class:`keystoneclient.auth.identity.v3.Auth` directly.

The new :py:class:`~keystoneclient.auth.identity.v3.AuthMethod` should take all
the required parameters via
:py:meth:`~keystoneclient.auth.identity.v3.AuthMethod.__init__` and return from
:py:meth:`~keystoneclient.auth.identity.v3.AuthMethod.get_auth_data` a tuple
with the unique identifier of this plugin (e.g. *password*) and a dictionary
containing the payload of values to send to the authentication server. The
session, calling auth object and request headers are also passed to this
function so that the plugin may use or manipulate them.

You should also provide a class that inherits from
:py:class:`keystoneclient.auth.identity.v3.Auth` with an instance of your new
:py:class:`~keystoneclient.auth.identity.v3.AuthMethod` as the `auth_methods`
parameter to :py:class:`keystoneclient.auth.identity.v3.Auth`.

By convention (and like above) these are named `PluginType` and
`PluginTypeMethod` (for example
:py:class:`~keystoneclient.auth.identity.v3.Password` and
:py:class:`~keystoneclient.auth.identity.v3.PasswordMethod`).


Creating a Custom Plugin
------------------------

To implement an entirely new plugin you should implement the base class
:py:class:`keystoneclient.auth.base.BaseAuthPlugin` and provide the
:py:meth:`~keystoneclient.auth.base.BaseAuthPlugin.get_endpoint`,
:py:meth:`~keystoneclient.auth.base.BaseAuthPlugin.get_token` and
:py:meth:`~keystoneclient.auth.base.BaseAuthPlugin.invalidate` functions.

:py:meth:`~keystoneclient.auth.base.BaseAuthPlugin.get_token` is called to
retrieve the string token from a plugin. It is intended that a plugin will
cache a received token and so if the token is still valid then it should be
re-used rather than fetching a new one. A session object is provided with which
the plugin can contact it's server. (Note: use `authenticated=False` when
making those requests or it will end up being called recursively). The return
value should be the token as a string.

:py:meth:`~keystoneclient.auth.base.BaseAuthPlugin.get_endpoint` is called to
determine a base URL for a particular service's requests. The keyword arguments
provided to the function are those that are given by the `endpoint_filter`
variable in :py:meth:`keystoneclient.session.Session.request`. A session object
is also provided so that the plugin may contact an external source to determine
the endpoint.  Again this will be generally be called once per request and so
it is up to the plugin to cache these responses if appropriate. The return
value should be the base URL to communicate with.

:py:meth:`~keystoneclient.auth.base.BaseAuthPlugin.invalidate` should also be
implemented to clear the current user credentials so that on the next
:py:meth:`~keystoneclient.auth.base.BaseAuthPlugin.get_token` call a new token
can be retrieved.

The most simple example of a plugin is the
:py:class:`keystoneclient.auth.token_endpoint.Token` plugin.

When writing a plugin you should ensure that any fetch operation is thread
safe. A common pattern is for a service to hold a single service authentication
plugin globally and re-use that between all threads. This means that when a
token expires there may be multiple threads that all try to fetch a new plugin
at the same time. It is the responsibility of the plugin to ensure that this
case is handled in a way that still results in correct reauthentication.
