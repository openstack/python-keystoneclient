Python bindings to the OpenStack Keystone API
=============================================

This is a client for the OpenStack Keystone API. There's a Python API (the
``keystoneclient`` module), and a command-line script (``keystone``). The
Keystone 2.0 API is still a moving target, so this module will remain in
"Beta" status until the API is finalized and fully implemented.

Development takes place on GitHub__. Bug reports and patches may be filed there.

__ https://github.com/4P/python-keystoneclient

This code a fork of `Rackspace's python-novaclient`__ which is in turn a fork of
`Jacobian's python-cloudservers`__. The python-keystoneclient is licensed under
the Apache License like the rest of OpenStack.

__ http://github.com/rackspace/python-novaclient
__ http://github.com/jacobian/python-cloudservers

.. contents:: Contents:
   :local:

Python API
----------

By way of a quick-start::

    # use v2.0 auth with http://example.com:5000/v2.0/")
    >>> from keystoneclient.v2_0 import client
    >>> keystone = client.Client(USERNAME, API_KEY, PROJECT_ID)
    >>> keystone.tenants.list()
    >>> tenant = keystone.tenants.create(name="test", descrption="My new tenant!", enabled=True)
    >>> tenant.delete()


Command-line API
----------------

.. attention:: COMING SOON

    The API is not yet implemented, but will follow the pattern laid
    out below.

Installing this package gets you a shell command, ``keystone``, that you
can use to interact with Keystone's API.

You'll need to provide your OpenStack username and API key. You can do this
with the ``--username``, ``--apikey`` and  ``--projectid`` params, but it's
easier to just set them as environment variables::

    export KEYSTONE_USERNAME=openstack
    export KEYSTONE_API_KEY=yadayada
    export KEYSTONE_PROJECTID=yadayada

You will also need to define the authentication url with ``--url`` and the
version of the API with ``--version``.  Or set them as an environment
variables as well::

    export KEYSTONE_URL=http://example.com:5000/v2.0
    export KEYSTONE_ADMIN_URL=http://example.com:35357/v2.0
    export KEYSTONE_VERSION=2.0

Since Keystone can return multiple regions in the Service Catalog, you
can specify the one you want with ``--region_name`` (or
``export KEYSTONE_REGION_NAME``). It defaults to the first in the list returned.

You'll find complete documentation on the shell by running
``keystone help``::

    usage: keystone [--username USERNAME] [--apikey APIKEY] [--projectid PROJECTID]
                   [--url URL] [--version VERSION] [--region_name NAME]
                   <subcommand> ...

    Command-line interface to the OpenStack Keystone API.

    Positional arguments:
      <subcommand>
        add-fixed-ip        Add a new fixed IP address to a servers network.


    Optional arguments:
      --username USERNAME   Defaults to env[KEYSTONE_USERNAME].
      --apikey APIKEY       Defaults to env[KEYSTONE_API_KEY].
      --apikey PROJECTID    Defaults to env[KEYSTONE_PROJECT_ID].
      --url AUTH_URL        Defaults to env[KEYSTONE_URL] or
      --url ADMIN_URL       Defaults to env[KEYSTONE_ADMIN_URL]
      --version VERSION     Defaults to env[KEYSTONE_VERSION] or 2.0.
      --region_name NAME    The region name in the Keystone Service Catalog
                            to use after authentication. Defaults to
                            env[KEYSTONE_REGION_NAME] or the first item
                            in the list returned.

    See "keystone help COMMAND" for help on a specific command.
