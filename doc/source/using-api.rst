==============
The client API
==============

Introduction
============
The main concepts in the Keystone API are:

 * tenants
 * users
 * roles
 * services
 * endpoints

The Keystone API lets you query and make changes through managers. For example,
to maipulate tenants, you interact with a
``keystoneclient.v2_0.tenants.TenantManger`` object.

You obtain access to managers through via atributes of the ``keystoneclient.v2_0.client.Client`` object. For example, the ``tenants`` attribute of the ``Client``
class is a tenant manager::

    >>> from keystoneclient.v2_0 import client
    >>> keystone = client.Client(...)
    >>> keystone.tenants.list() # List tenants

You create a valid ``keystoneclient.v2_0.client.Client`` object by passing
authentication data to the constructor. Authentication and examples of common
tasks are provided below.

Authenticating
==============

There are two ways to authenticate against Keystone:
 * against the admin endpoint with the admin token
 * against the public endpoint with a username and password

If you are an administrator, you can authenticate by connecting to the admin
endpoint and using the admin token (sometimes referred to as the service
token). The token is specified as the ``admin_token`` configuration option in your
keystone.conf config file, which is typically in /etc/keystone::

    >>> from keystoneclient.v2_0 import client
    >>> token = '012345SECRET99TOKEN012345'
    >>> endpoint = 'http://192.168.206.130:35357/v2.0'
    >>> keystone = client.Client(token=token, endpoint=endpoint)

If you have a username and password, authentication is done against the
public endpoint. You must also specify a tenant that is associated with the
user::

    >>> from keystoneclient.v2_0 import client
    >>> username='adminUser'
    >>> password='secreetword'
    >>> tenant_name='openstackDemo'
    >>> auth_url='http://192.168.206.130:5000/v2.0'
    >>> keystone = client.Client(username=username, password=password,
    ...                         tenant_name, auth_url=auth_url)

Creating tenants
================

This example will create a tenant named *openStackDemo*::

    >>> from keystoneclient.v2_0 import client
    >>> keystone = client.Client(...)
    >>> keystone.tenants.create(tenant_name="openstackDemo",
    ...                         description="Default Tenant", enabled=True)
    <Tenant {u'id': u'9b7962da6eb04745b477ae920ad55939', u'enabled': True, u'description': u'Default Tenant', u'name': u'openstackDemo'}>

Creating users
==============

This example will create a user named *adminUser* with a password *secretword*
in the opoenstackDemo tenant. We first need to retrieve the tenant::

    >>> from keystoneclient.v2_0 import client
    >>> keystone = client.Client(...)
    >>> tenants = keystone.tenants.list()
    >>> my_tenant = [x for x in tenants if x.name=='openstackDemo'][0]
    >>> my_user = keystone.users.create(name="adminUser", password="secretword",
    ...                                                   tenant_id=my_tenant.id)

Creating roles and adding users
===============================

This example will create an admin role and add the *my_user* user to that
role, but only for the *my_tenant* tenant:

    >>> from keystoneclient.v2_0 import client
    >>> keystone = client.Client(...)
    >>> role = keystone.roles.create('admin')
    >>> my_tenant = ...
    >>> my_user = ...
    >>> keystone.roles.add_user_role(my_user, role, my_tenant)

Creating services and endpoints
===============================

This example will create the service and corresponding endpoint for the
Compute service::

    >>> from keystoneclient.v2_0 import client
    >>> keystone = client.Client(...)
    >>> service = keystone.services.create(name="nova", service_type="compute",
    ...                                    description="Nova Compute Service")
    >>> keystone.endpoints.create(region="RegionOne", service_id=service.id,
    ...            publicurl="http://192.168.206.130:8774/v2/%(tenant_id)s",
    ...            adminurl="http://192.168.206.130:8774/v2/%(tenant_id)s",
    ...            internalurl="http://192.168.206.130:8774/v2/%(tenant_id)s")
