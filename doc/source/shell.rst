The :program:`keystone` shell utility
=====================================

.. program:: keystone
.. highlight:: bash


The :program:`keystone` shell utility interacts with OpenStack Keystone API
from the command line. It supports the entirety of the OpenStack Keystone API.

To communicate with the API, you will need to be authenticated - and the
:program:`keystone` provides multiple options for this.

While bootstrapping keystone the authentication is accomplished with a
shared secret token and the location of the keystone API endpoint. The
shared secret token is configured in keystone.conf as "admin_token".

You can specify those values on the command line with :option:`--os-token`
and :option:`--os-endpoint`, or set them in environment variables:

.. envvar:: OS_SERVICE_TOKEN

    Your keystone administrative token

.. envvar:: OS_SERVICE_ENDPOINT

    Your keystone API endpoint

The command line options will override any environment variables set.

If you already have accounts, you can use your OpenStack username and
password. You can do this with the :option:`--os-username`,
:option:`--os-password`.

Keystone allows a user to be associated with one or more tenants. To specify
the tenant for which you want to authorize against, you may optionally
specify a :option:`--os-tenant-id` or :option:`--os-tenant-name`.

Instead of using options, it is easier to just set them as environment
variables:

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
