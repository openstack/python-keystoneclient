# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Nebula, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from keystoneclient.v2_0 import client
from keystoneclient import utils

CLIENT_CLASS = client.Client


@utils.arg('tenant',
           metavar='<tenant_id>',
           help='ID of Tenant. (Optional)',
           nargs='?',
           default=None)
def do_user_list(kc, args):
    users = kc.users.list(tenant_id=args.tenant)
    utils.print_list(users, ['id', 'enabled', 'email', 'name', 'tenantId'])


@utils.arg('--username', metavar='<username>', nargs='?',
           help='Desired username. (unique)')
@utils.arg('--password', metavar='<password>', nargs='?',
           help='Desired password.')
@utils.arg('--email', metavar='<email>', nargs='?',
           help='Desired email address. (unique)')
@utils.arg('--default-tenant', metavar='<default_tenant>', nargs='?',
           help='User will join the default tenant as a Member.')
@utils.arg('--enabled', metavar='<enabled>', nargs='?', default=True,
           help='Enable user immediately (Optional, default True)')
def do_user_create(kc, args):
    user = kc.users.create(args.username, args.password, args.email,
                           tenant_id=args.default_tenant, enabled=args.enabled)
    utils.print_dict(user._info)


@utils.arg('id', metavar='<user_id>', nargs='?',
           help='User ID to update email.')
@utils.arg('email', metavar='<email>', nargs='?',
           help='New desired email address.')
def do_user_update_email(kc, args):
    user = kc.users.update_email(args.id, args.email)
    utils.print_dict(user._info)


@utils.arg('id', metavar='<user_id>', nargs='?', help='User ID to enable.')
def do_user_enable(kc, args):
    try:
        kc.users.update_enabled(args.id, True)
        print 'User has been enabled.'
    except:
        'Unable to enable user.'


@utils.arg('id', metavar='<user_id>', nargs='?', help='User ID to disable.')
def do_user_disable(kc, args):
    try:
        kc.users.update_enabled(args.id, False)
        print 'User has been disabled.'
    except:
        'Unable to disable user.'


@utils.arg('id', metavar='<user_id>', nargs='?', help='User ID to update.')
@utils.arg('password', metavar='<password>', nargs='?',
           help='New desired password.')
def do_user_update_password(kc, args):
    try:
        kc.users.update_password(args.id, args.password)
        print 'User password has been udpated.'
    except:
        'Unable to update users password.'


@utils.arg('id', metavar='<user_id>', nargs='?', help='User ID to delete.')
def do_user_delete(kc, args):
    try:
        kc.users.delete(args.id)
        print 'User has been deleted.'
    except:
        'Unable to delete user.'


@utils.arg('--tenant-name', metavar='<tenant_name>', nargs='?',
           help='Desired name of new tenant.')
@utils.arg('--description', metavar='<description>', nargs='?', default=None,
           help='Useful description of new tenant (optional, default is None)')
@utils.arg('--enabled', metavar='<enabled>', nargs='?', default=True,
           help='Enable user immediately (Optional, default True)')
def do_tenant_create(kc, args):
    tenant = kc.tenants.create(args.tenant_name,
                             description=args.description,
                             enabled=args.enabled)
    utils.print_dict(tenant._info)


@utils.arg('id', metavar='<tenant_id>', nargs='?', help='Tenant ID to enable.')
def do_tenant_enable(kc, args):
    try:
        kc.tenants.update(args.id, enabled=True)
        print 'Tenant has been enabled.'
    except:
        'Unable to enable tenant.'


@utils.arg('id', metavar='<tenant_id>', nargs='?', help='Tenant ID to disable')
def do_tenant_disable(kc, args):
    try:
        kc.tenants.update_enabled(args.id, enabled=False)
        print 'Tenant has been disabled.'
    except:
        'Unable to disable tenant.'


@utils.arg('id', metavar='<tenant_id>', nargs='?', help='Tenant ID to delete')
def do_tenant_delete(kc, args):
    try:
        kc.tenants.delete(args.id)
        print 'Tenant has been deleted.'
    except:
        'Unable to delete tenant.'


@utils.arg('--service-name', metavar='<service_name>', nargs='?',
           help='Desired name of service. (unique)')
# TODO(jakedahn): add service type examples to helptext.
@utils.arg('--service-type', metavar='<service_type>', nargs='?',
           help='Possible service types: identity, compute, network, \
                 image, or object-store.')
@utils.arg('--description', metavar='<service_description>', nargs='?',
           help='Useful description of service.')
def do_service_create(kc, args):
    service = kc.services.create(args.service_name,
                                 args.service_type,
                                 args.description)
    utils.print_dict(service._info)


def do_service_list(kc, args):
    services = kc.services.list()
    utils.print_list(services, ['id', 'name', 'type', 'description'])


@utils.arg('id',
           metavar='<service_id>',
           help='ID of Service to retrieve.',
           nargs='?')
def do_service_get(kc, args):
    service = kc.services.get(args.id)
    utils.print_dict(service._info)


@utils.arg('id',
           metavar='<service_id>',
           help='ID of Service to delete',
           nargs='?')
def do_service_get(kc, args):
    try:
        kc.services.delete(args.id)
        print 'Service has been deleted'
    except:
        print 'Unable to delete service.'


def do_role_list(kc, args):
    roles = kc.roles.list()
    utils.print_list(roles, ['id', 'name'])


@utils.arg('id', metavar='<role_id>', help='ID of Role to fetch.', nargs='?')
def do_role_get(kc, args):
    role = kc.roles.get(args.id)
    utils.print_dict(role._info)


@utils.arg('role-name', metavar='<role_name>', nargs='?',
           help='Desired name of new role.')
def do_role_create(kc, args):
    role = kc.roles.create(args.role_name)
    utils.print_dict(role._info)


@utils.arg('id', metavar='<role_id>', help='ID of Role to delete.', nargs='?')
def do_role_delete(kc, args):
    try:
        kc.roles.delete(args.id)
        print 'Role has been deleted.'
    except:
        print 'Unable to delete role.'


@utils.arg('id', metavar='<user_id>', help='ID of User', nargs='?')
def do_user_roles(kc, args):
    roles = kc.roles.get_user_role_refs(args.id)
    for role in roles:
        try:
            role.tenant = kc.tenants.get(role.tenantId).name
        except Exception, e:
            role.tenant = 'n/a'
        role.name = kc.roles.get(role.roleId).name
    utils.print_list(roles, ['tenant', 'name'])


# TODO(jakedahn): refactor this to allow role, user, and tenant names.
@utils.arg('tenant_id', metavar='<tenant_id>', help='ID of Tenant', nargs='?')
@utils.arg('user_id', metavar='<user_id>', help='ID of User', nargs='?')
@utils.arg('role_id', metavar='<role_id>', help='ID of Role', nargs='?')
def do_user_add_tenant_role(kc, args):
    kc.roles.add_user_to_tenant(args.tenant_id, args.user_id, args.role_id)


# TODO(jakedahn): refactor this to allow role, user, and tenant names.
@utils.arg('tenant_id', metavar='<tenant_id>', help='ID of Tenant', nargs='?')
@utils.arg('user_id', metavar='<user_id>', help='ID of User', nargs='?')
@utils.arg('role_id', metavar='<role_id>', help='ID of Role', nargs='?')
def do_user_remove_tenant_role(kc, args):
    kc.roles.remove_user_to_tenant(args.tenant_id, args.user_id, args.role_id)


@utils.arg('tenant_id', metavar='<tenant_id>', help='ID of Tenant', nargs='?')
@utils.arg('user_id', metavar='<user_id>', help='ID of User', nargs='?')
def do_ec2_create_credentials(kc, args):
    credentials = kc.ec2.create(args.user_id, args.tenant_id)
    utils.print_dict(credentials._info)


@utils.arg('user_id', metavar='<user_id>', help='ID of User', nargs='?')
def do_ec2_list_credentials(kc, args):
    credentials = kc.ec2.list(args.user_id)
    for cred in credentials:
        cred.tenant = kc.tenants.get(cred.tenant_id).name
    utils.print_list(credentials, ['tenant', 'key', 'secret'])


@utils.arg('user_id', metavar='<user_id>', help='ID of User', nargs='?')
@utils.arg('key', metavar='<access_key>', help='Access Key', nargs='?')
def do_ec2_delete_credentials(kc, args):
    try:
        kc.ec2.delete(args.user_id, args.key)
        print 'Deleted EC2 Credentials.'
    except:
        print 'Unable to delete EC2 Credentials.'
