Keystone Style Commandments
===========================

- Step 1: Read the OpenStack Style Commandments
  http://docs.openstack.org/developer/hacking/
- Step 2: Read on

Exceptions
----------

When dealing with exceptions from underlying libraries, translate those
exceptions to an instance or subclass of ClientException.

=======
Testing
=======

python-keystoneclient uses testtools and testr for its unittest suite
and its test runner. Basic workflow around our use of tox and testr can
be found at http://wiki.openstack.org/testr. If you'd like to learn more
in depth:

  https://testtools.readthedocs.org/
  https://testrepository.readthedocs.org/
