from keystoneclient import utils
from keystoneclient.v2_0 import client


@utils.arg('--user-name', metavar='<user-name>', default='admin', dest='user',
           help='The name of the user to be created (default="admin").')
@utils.arg('--pass', metavar='<password>', required=True, dest='passwd',
           help='The password for the new user.')
@utils.arg('--role-name', metavar='<role-name>', default='admin', dest='role',
           help='The name of the role to be created and granted to the user '
           '(default="admin").')
@utils.arg('--tenant-name', metavar='<tenant-name>', default='admin',
           dest='tenant',
           help='The name of the tenant to be created (default="admin").')
def do_bootstrap(kc, args):
    """Grants a new role to a new user on a new tenant, after creating each."""
    tenant = kc.tenants.create(tenant_name=args.tenant)
    role = kc.roles.create(name=args.role)
    user = kc.users.create(name=args.user, password=args.passwd, email=None)
    kc.roles.add_user_role(user=user, role=role, tenant=tenant)

    # verify the result
    user_client = client.Client(
        username=args.user,
        password=args.passwd,
        tenant_name=args.tenant,
        auth_url=kc.management_url)
    user_client.authenticate()
