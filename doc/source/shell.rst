The :program:`keystone` shell utility
=========================================

.. program:: keystone
.. highlight:: bash


The :program:`keystone` shell utility interacts with OpenStack Keystone API
from the command line. It supports the entirety of the OpenStack Keystone API.

First, you'll need an OpenStack Keystone account. You get this by using the 
`keystone-manage` command in OpenStack Keystone.

You'll need to provide :program:`keystone` with your OpenStack username and
password. You can do this with the :option:`--os-username`, :option:`--os-password`.
You can optionally specify a :option:`--os-tenant-id` or :option:`--os-tenant-name`,
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

.. envvar:: OS_CACERT

    The location for the CA truststore (PEM formatted) for this client.

.. envvar:: OS_CERT

    The location for the keystore (PEM formatted) containing the public
    key of this client.  This keystore can also optionally contain the
    private key of this client.

.. envvar:: OS_KEY

    The location for the keystore (PEM formatted) containing the private
    key of this client.  This value can be empty if the private key is
    included in the OS_CERT file.

For example, in Bash you'd use::

    export OS_USERNAME=yourname
    export OS_PASSWORD=yadayadayada
    export OS_TENANT_NAME=myproject
    export OS_AUTH_URL=http(s)://example.com:5000/v2.0/
    export OS_IDENTITY_API_VERSION=2.0
    export OS_CACERT=/etc/keystone/yourca.pem
    export OS_CERT=/etc/keystone/yourpublickey.pem
    export OS_KEY=/etc/keystone/yourprivatekey.pem

From there, all shell commands take the form::

    keystone <command> [arguments...]

Run :program:`keystone help` to get a full list of all possible commands,
and run :program:`keystone help <command>` to get detailed help for that
command.
