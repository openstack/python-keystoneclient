=================
The Client v3 API
=================

Introduction
============

The main concepts in the Identity v3 API are:

 * credentials
 * domains
 * endpoints
 * groups
 * policies
 * projects
 * role assignments
 * roles
 * services
 * trusts
 * users

The :py:mod:`keystoneclient.v3.client` API lets you query and make changes
through ``managers``. For example, to manipulate a project (formerly
called tenant), you interact with a
:py:class:`keystoneclient.v3.projects.ProjectManager` object.

You obtain access to managers through attributes of a
:py:class:`keystoneclient.v3.client.Client` object. For example, the
``projects`` attribute of a ``Client`` object is a projects manager::

    >>> from keystoneclient.v3 import client
    >>> keystone = client.Client(...)
    >>> keystone.projects.list() # List projects

While it is possible to instantiate a
:py:class:`keystoneclient.v3.client.Client` object (as done above for
clarity), the recommended approach is to use the discovery mechanism
provided by the :py:class:`keystoneclient.client.Client` class. The
appropriate class will be instantiated depending on the API versions
available::

    >>> from keystoneclient import client
    >>> keystone =
    ...    client.Client(auth_url='http://localhost:5000', ...)
    >>> type(keystone)
    <class 'keystoneclient.v3.client.Client'>

One can force the use of a specific version of the API, either by
using the ``version`` keyword argument::

    >>> from keystoneclient import client
    >>> keystone = client.Client(auth_url='http://localhost:5000',
                                 version=(2,), ...)
    >>> type(keystone)
    <class 'keystoneclient.v2_0.client.Client'>
    >>> keystone = client.Client(auth_url='http://localhost:5000',
                                 version=(3,), ...)
    >>> type(keystone)
    <class 'keystoneclient.v3.client.Client'>

Or by specifying directly the specific API version authentication URL
as the auth_url keyword argument::

    >>> from keystoneclient import client
    >>> keystone =
    ...     client.Client(auth_url='http://localhost:5000/v2.0', ...)
    >>> type(keystone)
    <class 'keystoneclient.v2_0.client.Client'>
    >>> keystone =
    ...     client.Client(auth_url='http://localhost:5000/v3', ...)
    >>> type(keystone)
    <class 'keystoneclient.v3.client.Client'>

Upon successful authentication, a :py:class:`keystoneclient.v3.client.Client`
object is returned (when using the Identity v3 API). Authentication and
examples of common tasks are provided below.

You can generally expect that when the client needs to propagate an
exception it will raise an instance of subclass of
``keystoneclient.exceptions.ClientException`` (see
:py:class:`keystoneclient.openstack.common.apiclient.exceptions.ClientException`)

Authenticating
==============

You can authenticate against Keystone using a username, a user domain
name (which will default to 'Default' if it is not specified) and a
password::

    >>> from keystoneclient import client
    >>> auth_url = 'http://localhost:5000'
    >>> username = 'adminUser'
    >>> user_domain_name = 'Default'
    >>> password = 'secreetword'
    >>> keystone = client.Client(auth_url=auth_url, version=(3,),
    ...                          username=username, password=password,
    ...                          user_domain_name=user_domain_name)

You may optionally specify a domain or project (along with its project
domain name), to obtain a scoped token::

    >>> from keystoneclient import client
    >>> auth_url = 'http://localhost:5000'
    >>> username = 'adminUser'
    >>> user_domain_name = 'Default'
    >>> project_name = 'demo'
    >>> project_domain_name = 'Default'
    >>> password = 'secreetword'
    >>> keystone = client.Client(auth_url=auth_url, version=(3,),
    ...                          username=username, password=password,
    ...                          user_domain_name=user_domain_name,
    ...                          project_name=project_name,
    ...                          project_domain_name=project_domain_name)

Using Sessions
==============

It's also possible to instantiate a :py:class:`keystoneclient.v3.client.Client`
class by using :py:class:`keystoneclient.session.Session`.::

    >>> from keystoneclient.auth.identity import v3
    >>> from keystoneclient import session
    >>> from keystoneclient.v3 import client
    >>> auth = v3.Password(auth_url='https://my.keystone.com:5000/v3',
    ...                    user_id='myuserid',
    ...                    password='mypassword',
    ...                    project_id='myprojectid')
    >>> sess = session.Session(auth=auth)
    >>> keystone = client.Client(session=sess)

For more information on Sessions refer to: `Using Sessions`_.

.. _`Using Sessions`: using-sessions.html
