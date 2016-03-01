==============
Using Sessions
==============

Introduction
============

The :py:class:`keystoneauth1.session.Session` class was introduced into
keystoneclient as an attempt to bring a unified interface to the various
OpenStack clients that share common authentication and request parameters
between a variety of services.

The model for using a Session and auth plugin as well as the general terms used
have been heavily inspired by the `requests <http://docs.python-requests.org>`_
library. However neither the Session class nor any of the authentication
plugins rely directly on those concepts from the requests library so you should
not expect a direct translation.

Features
--------

- Common client authentication

  Authentication is handled by one of a variety of authentication plugins and
  then this authentication information is shared between all the services that
  use the same Session object.

- Security maintenance

  Security code is maintained in a single place and reused between all
  clients such that in the event of problems it can be fixed in a single
  location.

- Standard discovery mechanisms

  Clients are not expected to have any knowledge of an identity token or any
  other form of identification credential. Service and endpoint discovery are
  handled by the Session and plugins.


Sessions for Users
==================

The Session object is the contact point to your OpenStack cloud services. It
stores the authentication credentials and connection information required to
communicate with OpenStack such that it can be reused to communicate with many
services.  When creating services this Session object is passed to the client
so that it may use this information.

A Session will authenticate on demand. When a request that requires
authentication passes through the Session the authentication plugin will be
asked for a valid token. If a valid token is available it will be used
otherwise the authentication plugin may attempt to contact the authentication
service and fetch a new one.

An example from keystoneclient::

    >>> from keystoneauth1.identity import v3
    >>> from keystoneauth1 import session
    >>> from keystoneclient.v3 import client

    >>> auth = v3.Password(auth_url='https://my.keystone.com:5000/v3',
    ...                    username='myuser',
    ...                    password='mypassword',
    ...                    project_id='proj',
    ...                    user_domain_id='domain')
    >>> sess = session.Session(auth=auth,
    ...                        verify='/path/to/ca.cert')
    >>> ks = client.Client(session=sess)
    >>> users = ks.users.list()

As clients adopt this means of operating they will be created in a similar
fashion by passing the Session object to the client's constructor.


Migrating keystoneclient to use a Session
-----------------------------------------

By using a session with a keystoneclient Client we presume that you have opted
in to new behavior defined by the session. For example authentication is now
on-demand rather than on creation. To allow this change in behavior there are
a number of functions that have changed behavior or are no longer available.

For example the
:py:meth:`keystoneclient.httpclient.HTTPClient.authenticate` method used
to be able to always re-authenticate the current client and fetch a new token.
As this is now controlled by the Session and not the client this has changed,
however the function will still exist to provide compatibility with older
clients.

Likewise certain parameters such as ``user_id`` and ``auth_token`` that used to
be available on the client object post authentication will remain
uninitialized.

When converting an application to use a session object with keystoneclient you
should be aware of the possibility of changes to authentication and
authentication parameters and make sure to test your code thoroughly. It should
have no impact on the typical CRUD interaction with the client.


Sharing Authentication Plugins
------------------------------

A session can only contain one authentication plugin however there is nothing
that specifically binds the authentication plugin to that session, a new
Session can be created that reuses the existing authentication plugin::

    >>> new_sess = session.Session(auth=sess.auth,
                                   verify='/path/to/different-cas.cert')

In this case we cannot know which session object will be used when the plugin
performs the authentication call so the command must be able to succeed with
either.

Authentication plugins can also be provided on a per-request basis. This will
be beneficial in a situation where a single session is juggling multiple
authentication credentials::

    >>> sess.get('https://my.keystone.com:5000/v3',
                 auth=my_auth_plugin)

If an auth plugin is provided via parameter then it will override any auth
plugin on the session.

Sessions for Client Developers
==============================

Sessions are intended to take away much of the hassle of dealing with
authentication data and token formats. Clients should be able to specify filter
parameters for selecting the endpoint and have the parsing of the catalog
managed for them.

Authentication
--------------

When making a request with a session object you can simply pass the keyword
parameter ``authenticated`` to indicate whether the argument should contain a
token, by default a token is included if an authentication plugin is available::

    >>> # In keystone this route is unprotected by default
    >>> resp = sess.get('https://my.keystone.com:5000/v3',
                        authenticated=False)


Service Discovery
-----------------

In OpenStack the URLs of available services are distributed to the user as a
part of the token they receive called the Service Catalog. Clients are expected
to use the URLs from the Service Catalog rather than have them provided.

In general a client does not need to know the full URL for the server that they
are communicating with, simply that it should send a request to a path
belonging to the correct service.

This is controlled by the ``endpoint_filter`` parameter to a request which
contains all the information an authentication plugin requires to determine the
correct URL to which to send a request. When using this mode only the path for
the request needs to be specified::

    >>> resp = session.get('/v3/users',
                           endpoint_filter={'service_type': 'identity',
                                            'interface': 'public',
                                            'region_name': 'myregion'})

``endpoint_filter`` accepts a number of arguments with which it can determine
an endpoint url:

- ``service_type``: the type of service. For example ``identity``, ``compute``,
  ``volume`` or many other predefined identifiers.

- ``interface``: the network exposure the interface has. This will be one of:

  - ``public``: An endpoint that is available to the wider internet or network.
  - ``internal``: An endpoint that is only accessible within the private network.
  - ``admin``: An endpoint to be used for administrative tasks.

- ``region_name``: the name of the region where the endpoint resides.

The endpoint filter is a simple key-value filter and can be provided with any
number of arguments. It is then up to the auth plugin to correctly use the
parameters it understands.

The session object determines the URL matching the filter and append to it the
provided path and so create a valid request. If multiple URL matches are found
then any one may be chosen.

While authentication plugins will endeavour to maintain a consistent set of
arguments for an ``endpoint_filter`` the concept of an authentication plugin is
purposefully generic and a specific mechanism may not know how to interpret
certain arguments and ignore them. For example the
:py:class:`keystoneauth1.identity.generic.token.Token` plugin (which is used
when you want to always use a specific endpoint and token combination) will
always return the same endpoint regardless of the parameters to
``endpoint_filter`` or a custom OpenStack authentication mechanism may not have
the concept of multiple ``interface`` options and choose to ignore that
parameter.

There is some expectation on the user that they understand the limitations of
the authentication system they are using.
