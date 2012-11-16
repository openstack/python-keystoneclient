Python bindings to the OpenStack Identity API (Keystone)
========================================================

This is a client for the OpenStack Identity API, implemented by Keystone.
There's a Python API (the ``keystoneclient`` module), and a command-line script
(``keystone``).

Development takes place via the usual OpenStack processes as outlined in the
`OpenStack wiki`_.  The master repository is on GitHub__.

__ http://wiki.openstack.org/HowToContribute
__ http://github.com/openstack/python-keystoneclient

This code a fork of `Rackspace's python-novaclient`__ which is in turn a fork
of `Jacobian's python-cloudservers`__. The python-keystoneclient is licensed
under the Apache License like the rest of OpenStack.

__ http://github.com/rackspace/python-novaclient
__ http://github.com/jacobian/python-cloudservers

.. contents:: Contents:
   :local:

Python API
----------

By way of a quick-start::

    # use v2.0 auth with http://example.com:5000/v2.0
    >>> from keystoneclient.v2_0 import client
    >>> keystone = client.Client(username=USERNAME, password=PASSWORD, tenant_name=TENANT, auth_url=AUTH_URL)
    >>> keystone.tenants.list()
    >>> tenant = keystone.tenants.create(tenant_name="test", description="My new tenant!", enabled=True)
    >>> tenant.delete()


Command-line API
----------------

Installing this package gets you a shell command, ``keystone``, that you can
use to interact with OpenStack's Identity API.

You'll need to provide your OpenStack tenant, username and password. You can do
this with the ``--os-tenant-name``, ``--os-username`` and ``--os-password``
params, but it's easier to just set them as environment variables::

    export OS_TENANT_NAME=project
    export OS_USERNAME=user
    export OS_PASSWORD=pass

You will also need to define the authentication url with ``--os-auth-url`` and
the version of the API with ``--os-identity-api-version``.  Or set them as an
environment variables as well::

    export OS_AUTH_URL=http://example.com:5000/v2.0
    export OS_IDENTITY_API_VERSION=2.0

Alternatively, to bypass username/password authentication, you can provide a
pre-established token. In Keystone, this approach is necessary to bootstrap the
service with an administrative user, tenant & role (to do so, provide the
client with the value of your ``admin_token`` defined in ``keystone.conf`` in
addition to the URL of your admin API deployment, typically on port 35357)::

    export OS_SERVICE_TOKEN=thequickbrownfox-jumpsover-thelazydog
    export OS_SERVICE_ENDPOINT=http://example.com:35357/v2.0

Since the Identity service can return multiple regions in the service catalog,
you can specify the one you want with ``--os-region-name`` (or ``export
OS_REGION_NAME``)::

    export OS_REGION_NAME=north

.. WARNING::

    If a region is not specified and multiple regions are returned by the
    Identity service, the client may not access the same region consistently.

You'll find complete documentation on the shell by running ``keystone help``::

    usage: keystone [--os-username <auth-user-name>]
                    [--os-password <auth-password>]
                    [--os-tenant-name <auth-tenant-name>]
                    [--os-tenant-id <tenant-id>] [--os-auth-url <auth-url>]
                    [--os-region-name <region-name>]
                    [--os-identity-api-version <identity-api-version>]
                    [--os-token <service-token>]
                    [--os-endpoint <service-endpoint>]
                    [--os-cacert <ca-certificate>] [--os-cert <certificate>]
                    [--os-key <key>] [--insecure]
                    <subcommand> ...

    Command-line interface to the OpenStack Identity API.

    Positional arguments:
    <subcommand>
        catalog
        ec2-credentials-create
                            Create EC2-compatibile credentials for user per tenant
        ec2-credentials-delete
                            Delete EC2-compatibile credentials
        ec2-credentials-get
                            Display EC2-compatibile credentials
        ec2-credentials-list
                            List EC2-compatibile credentials for a user
        endpoint-create     Create a new endpoint associated with a service
        endpoint-delete     Delete a service endpoint
        endpoint-get
        endpoint-list       List configured service endpoints
        role-create         Create new role
        role-delete         Delete role
        role-get            Display role details
        role-list           List all roles
        service-create      Add service to Service Catalog
        service-delete      Delete service from Service Catalog
        service-get         Display service from Service Catalog
        service-list        List all services in Service Catalog
        tenant-create       Create new tenant
        tenant-delete       Delete tenant
        tenant-get          Display tenant details
        tenant-list         List all tenants
        tenant-update       Update tenant name, description, enabled status
        token-get
        user-create         Create new user
        user-delete         Delete user
        user-get            Display user details.
        user-list           List users
        user-password-update
                            Update user password
        user-role-add       Add role to user
        user-role-list      List roles granted to a user
        user-role-remove    Remove role from user
        user-update         Update user's name, email, and enabled status
        discover            Discover Keystone servers and show authentication
                            protocols and
        bootstrap           Grants a new role to a new user on a new tenant, after
                            creating each.
        bash-completion     Prints all of the commands and options to stdout.
        help                Display help about this program or one of its
                            subcommands.

    Optional arguments:
    --os-username <auth-user-name>
                            Name used for authentication with the OpenStack
                            Identity service. Defaults to env[OS_USERNAME]
    --os-password <auth-password>
                            Password used for authentication with the OpenStack
                            Identity service. Defaults to env[OS_PASSWORD]
    --os-tenant-name <auth-tenant-name>
                            Tenant to request authorization on. Defaults to
                            env[OS_TENANT_NAME]
    --os-tenant-id <tenant-id>
                            Tenant to request authorization on. Defaults to
                            env[OS_TENANT_ID]
    --os-auth-url <auth-url>
                            Specify the Identity endpoint to use for
                            authentication. Defaults to env[OS_AUTH_URL]
    --os-region-name <region-name>
                            Defaults to env[OS_REGION_NAME]
    --os-identity-api-version <identity-api-version>
                            Defaults to env[OS_IDENTITY_API_VERSION] or 2.0
    --os-token <service-token>
                            Specify an existing token to use instead of retrieving
                            one via authentication (e.g. with username &
                            password). Defaults to env[OS_SERVICE_TOKEN]
    --os-endpoint <service-endpoint>
                            Specify an endpoint to use instead of retrieving one
                            from the service catalog (via authentication).
                            Defaults to env[OS_SERVICE_ENDPOINT]
    --os-cacert <ca-certificate>
                            Defaults to env[OS_CACERT]
    --os-cert <certificate>
                            Defaults to env[OS_CERT]
    --os-key <key>        Defaults to env[OS_KEY]
    --insecure            Explicitly allow keystoneclient to perform "insecure"
                            SSL (https) requests. The server's certificate will
                            not be verified against any certificate authorities.
                            This option should be used with caution.

    See "keystone help COMMAND" for help on a specific command.
