Python bindings to the OpenStack Identity API (Keystone)
========================================================

.. image:: https://img.shields.io/pypi/v/python-keystoneclient.svg
    :target: https://pypi.python.org/pypi/python-keystoneclient/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/python-keystoneclient.svg
    :target: https://pypi.python.org/pypi/python-keystoneclient/
    :alt: Downloads

This is a client for the OpenStack Identity API, implemented by the Keystone
team; it contains a Python API (the ``keystoneclient`` module) for
OpenStack's Identity Service. For command line interface support, use
`OpenStackClient`_.

* `PyPi`_ - package installation
* `Online Documentation`_
* `Launchpad project`_ - release management
* `Blueprints`_ - feature specifications
* `Bugs`_ - issue tracking
* `Source`_
* `Specs`_
* `How to Contribute`_

.. _PyPi: https://pypi.python.org/pypi/python-keystoneclient
.. _Online Documentation: http://docs.openstack.org/developer/python-keystoneclient
.. _Launchpad project: https://launchpad.net/python-keystoneclient
.. _Blueprints: https://blueprints.launchpad.net/python-keystoneclient
.. _Bugs: https://bugs.launchpad.net/python-keystoneclient
.. _Source: https://git.openstack.org/cgit/openstack/python-keystoneclient
.. _OpenStackClient: https://pypi.python.org/pypi/python-openstackclient
.. _How to Contribute: http://docs.openstack.org/infra/manual/developers.html
.. _Specs: http://specs.openstack.org/openstack/keystone-specs/

.. contents:: Contents:
   :local:

Python API
----------

By way of a quick-start::

    >>> from keystoneauth1.identity import v3
    >>> from keystoneauth1 import session
    >>> from keystoneclient.v3 import client
    >>> auth = v3.Password(auth_url="http://example.com:5000/v3", username="admin",
    ...                     password="password", project_name="admin",
    ...                     user_domain_id="default", project_domain_id="default")
    >>> sess = session.Session(auth=auth)
    >>> keystone = client.Client(session=sess)
    >>> keystone.projects.list()
        [...]
    >>> project = keystone.projects.create(name="test", description="My new Project!", domain="default", enabled=True)
    >>> project.delete()
