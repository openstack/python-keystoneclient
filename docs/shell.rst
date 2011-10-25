The :program:`keystone` shell utility
=========================================

.. program:: keystone
.. highlight:: bash

.. warning:: COMING SOON

    The command line interface is not yet completed. This document serves
    as a reference for the implementation.

The :program:`keystone` shell utility interacts with OpenStack Keystone API
from the command line. It supports the entirety of the OpenStack Keystone API.

First, you'll need an OpenStack Keystone account and an API key. You get this
by using the `keystone-manage` command in OpenStack Keystone.

You'll need to provide :program:`keystone` with your OpenStack username and
API key. You can do this with the :option:`--username`, :option:`--apikey`
and :option:`--projectid` options, but it's easier to just set them as
environment variables by setting two environment variables:

.. envvar:: KEYSTONE_USERNAME

    Your Keystone username.

.. envvar:: KEYSTONE_API_KEY

    Your API key.

.. envvar:: KEYSTONE_PROJECT_ID

    Project for work.

.. envvar:: KEYSTONE_URL

    The OpenStack API server URL.

.. envvar:: KEYSTONE_VERSION

    The OpenStack API version.

For example, in Bash you'd use::

    export KEYSTONE_USERNAME=yourname
    export KEYSTONE_API_KEY=yadayadayada
    export KEYSTONE_PROJECT_ID=myproject
    export KEYSTONE_URL=http://...
    export KEYSTONE_VERSION=2.0

From there, all shell commands take the form::

    keystone <command> [arguments...]

Run :program:`keystone help` to get a full list of all possible commands,
and run :program:`keystone help <command>` to get detailed help for that
command.
