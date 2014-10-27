Python bindings to the OpenStack Identity API (Keystone)
========================================================

This is a client for OpenStack Identity API. There's a Python API for
:doc:`Identity API v3 <using-api-v3>` and :doc:`v2 <using-api-v2>` (the
:mod:`keystoneclient` modules), and a command-line script (installed as
:doc:`keystone <man/keystone>`).

Contents:

.. toctree::
   :maxdepth: 1

   man/keystone
   using-sessions
   using-api-v2
   using-api-v3

   authentication-plugins
   middlewarearchitecture

   api/modules

Contributing
============

Code is hosted `on GitHub`_. Submit bugs to the Keystone project on
`Launchpad`_. Submit code to the ``openstack/python-keystoneclient`` project
using `Gerrit`_.

.. _on GitHub: https://github.com/openstack/python-keystoneclient
.. _Launchpad: https://launchpad.net/python-keystoneclient
.. _Gerrit: http://wiki.openstack.org/GerritWorkflow

Run tests with ``python setup.py test``.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

