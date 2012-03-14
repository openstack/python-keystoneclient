Python bindings to the OpenStack Keystone API
=============================================

This is a client for the OpenStack Keystone API. There's a Python API (the
``keystoneclient`` module), and a command-line script (``keystone``). The
Keystone 2.0 API is still a moving target, so this module will remain in
"Beta" status until the API is finalized and fully implemented.

Development takes place via the usual OpenStack processes as outlined in
the `OpenStack wiki`_.  The master repository is on GitHub__.

__ http://wiki.openstack.org/HowToContribute
__ http://github.com/openstack/python-keystoneclient

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

    # use v2.0 auth with http://example.com:5000/v2.0")
    >>> from keystoneclient.v2_0 import client
    >>> keystone = client.Client(username=USERNAME, password=PASSWORD, tenant_name=TENANT, auth_url=KEYSTONE_URL)
    >>> keystone.tenants.list()
    >>> tenant = keystone.tenants.create(name="test", descrption="My new tenant!", enabled=True)
    >>> tenant.delete()


Command-line API
----------------

Installing this package gets you a shell command, ``keystone``, that you
can use to interact with Keystone's Identity API.

You'll need to provide your OpenStack tenant, username and password. You can
do this with the ``--os_tenant_name``, ``--os_username`` and ``--os_password``
params, but it's easier to just set them as environment variables::

    export OS_TENANT_NAME=project
    export OS_USERNAME=user
    export OS_PASSWORD=pass

You will also need to define the authentication url with ``--os_auth_url`` and the
version of the API with ``--identity_api_version``.  Or set them as an environment
variables as well::

    export OS_AUTH_URL=http://example.com:5000/v2.0
    export OS_IDENTITY_API_VERSION=2.0

Alternatively, to authenticate to Keystone without a username/password,
such as when there are no users in the database yet, use the service
token and endpoint arguemnts.  The service token is set in keystone.conf as
``admin_token``; set it with ``service_token``.  Note: keep the service token
secret as it allows total access to Keystone's database.  The admin endpoint is set
with ``--endpoint`` or ``SERVICE_ENDPOINT``::

    export SERVICE_TOKEN=thequickbrownfox-jumpsover-thelazydog
    export SERVICE_ENDPOINT=http://example.com:35357/v2.0

Since Keystone can return multiple regions in the Service Catalog, you
can specify the one you want with ``--region_name`` (or
``export OS_REGION_NAME``). It defaults to the first in the list returned.

You'll find complete documentation on the shell by running
``keystone help``::

    usage: keystone [--os_username OS_USERNAME] [--os_password OS_PASSWORD]
                    [--os_tenant_name OS_TENANT_NAME]
                    [--os_tenant_id OS_TENANT_ID] [--os_auth_url OS_AUTH_URL]
                    [--os_region_name OS_REGION_NAME]
                    [--identity_api_version IDENTITY_API_VERSION] [--token TOKEN]
                    [--endpoint ENDPOINT]
                    <subcommand> ...

    Command-line interface to the OpenStack Identity API.

    Positional arguments:
      <subcommand>
        catalog             List service catalog, possibly filtered by service.
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
        endpoint-get        Find endpoint filtered by a specific attribute or
                            service type
        endpoint-list       List configured service endpoints
        role-create         Create new role
        role-delete         Delete role
        role-get            Display role details
        role-list           List all available roles
        service-create      Add service to Service Catalog
        service-delete      Delete service from Service Catalog
        service-get         Display service from Service Catalog
        service-list        List all services in Service Catalog
        tenant-create       Create new tenant
        tenant-delete       Delete tenant
        tenant-get          Display tenant details
        tenant-list         List all tenants
        tenant-update       Update tenant name, description, enabled status
        token-get           Display the current user token
        user-create         Create new user
        user-delete         Delete user
        user-list           List users
        user-password-update
                            Update user password
        user-role-add       Add role to user
        user-role-remove    Remove role from user
        user-update         Update user's name, email, and enabled status
        discover            Discover Keystone servers and show authentication
                            protocols and
        help                Display help about this program or one of its
                            subcommands.

    Optional arguments:
      --os_username OS_USERNAME
                            Defaults to env[OS_USERNAME]
      --os_password OS_PASSWORD
                            Defaults to env[OS_PASSWORD]
      --os_tenant_name OS_TENANT_NAME
                            Defaults to env[OS_TENANT_NAME]
      --os_tenant_id OS_TENANT_ID
                            Defaults to env[OS_TENANT_ID]
      --os_auth_url OS_AUTH_URL
                            Defaults to env[OS_AUTH_URL]
      --os_region_name OS_REGION_NAME
                            Defaults to env[OS_REGION_NAME]
      --identity_api_version IDENTITY_API_VERSION
                            Defaults to env[OS_IDENTITY_API_VERSION] or 2.0
      --token TOKEN         Defaults to env[SERVICE_TOKEN]
      --endpoint ENDPOINT   Defaults to env[SERVICE_ENDPOINT]

See "keystone help COMMAND" for help on a specific command.
