=============
Release notes
=============

0.1.3 (August 31, 2012)
=======================
* changed logging to report request and response independently in --debug mode
* changed options to use hyphens instead of underscores
* added support for PKI signed tokens with Keystone


0.1.2 (July 9, 2012)
====================
* added support for two-way SSL and --insecure option to allow for self-signed
  certificates
* added support for password prompting if not provided
* added support for bash completion for keystone
* updated CLI options to use dashes instead of underscores

0.1.1 (June 25, 2012)
=====================
* corrected versioning

0.1.0 (March 29, 2012)
======================
* released with OpenStack Essex and Diablo compatibility
* forked from http://github.com/rackspace/python-novaclient
* refactored to support Identity API (auth, tokens, services, roles, tenants,
  users, etc.)
* removed legacy arguments of --username, --password, etc in migration to
  support a cross-openstack unified CLI convention defined at
  http://wiki.openstack.org/UnifiedCLI
* required service ID for listing endpoints
