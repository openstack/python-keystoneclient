The :program:`keystone` shell utility
=========================================

.. program:: keystone
.. highlight:: bash


The :program:`keystone` shell utility interacts with OpenStack Keystone API
from the command line. It supports the entirety of the OpenStack Keystone API.

First, you'll need an OpenStack Keystone account. You get this by using the 
`keystone-manage` command in OpenStack Keystone.

You'll need to provide :program:`keystone` with your OpenStack username and
password. You can do this with the :option:`--os_username`, :option:`--os_password`.
You can optionally specify a :option:`--os_tenant_id` or :option:`--os_tenant_name`,
to scope your token to a specific tenant.  If you don't specify a tenant, you
will be scoped to your default tenant if you have one.  Instead of using 
options, it is easier to just set them as environment variables:

.. envvar:: OS_USERNAME

    Your Keystone username.

.. envvar:: OS_PASSWORD

    Your Keystone password.

.. envvar:: OS_TENANT_NAME

    Name of Keystone Tenant.

.. envvar:: OS_TENANT_ID

    ID of Keystone Tenant.

.. envvar:: OS_AUTH_URL

    The OpenStack API server URL.

.. envvar:: OS_IDENTITY_API_VERSION

    The OpenStack Identity API version.

For example, in Bash you'd use::

    export OS_USERNAME=yourname
    export OS_PASSWORD=yadayadayada
    export OS_TENANT_NAME=myproject
    export OS_AUTH_URL=http://example.com:5000/v2.0/
    export OS_IDENTITY_API_VERSION=2.0

From there, all shell commands take the form::

    keystone <command> [arguments...]

Run :program:`keystone help` to get a full list of all possible commands,
and run :program:`keystone help <command>` to get detailed help for that
command.
