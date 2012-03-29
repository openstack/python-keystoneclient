# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
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

"""
Command-line interface to the OpenStack Identity API.
"""

import argparse
import httplib2
import os
import sys

from keystoneclient import exceptions as exc
from keystoneclient import utils
from keystoneclient.v2_0 import shell as shell_v2_0
from keystoneclient.generic import shell as shell_generic


def env(*vars, **kwargs):
    """Search for the first defined of possibly many env vars

    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.

    """
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


class OpenStackIdentityShell(object):

    def get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog='keystone',
            description=__doc__.strip(),
            epilog='See "keystone help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
            action='store_true',
            help=argparse.SUPPRESS,
        )

        parser.add_argument('--debug',
            default=False,
            action='store_true',
            help=argparse.SUPPRESS)

        parser.add_argument('--os_username', metavar='<auth-user-name>',
            default=env('OS_USERNAME'),
            help='Defaults to env[OS_USERNAME]')

        parser.add_argument('--os_password', metavar='<auth-password>',
            default=env('OS_PASSWORD'),
            help='Defaults to env[OS_PASSWORD]')

        parser.add_argument('--os_tenant_name', metavar='<auth-tenant-name>',
            default=env('OS_TENANT_NAME'),
            help='Defaults to env[OS_TENANT_NAME]')

        parser.add_argument('--os_tenant_id', metavar='<tenant-id>',
            default=env('OS_TENANT_ID'),
            help='Defaults to env[OS_TENANT_ID]')

        parser.add_argument('--os_auth_url', metavar='<auth-url>',
            default=env('OS_AUTH_URL'),
            help='Defaults to env[OS_AUTH_URL]')

        parser.add_argument('--os_region_name', metavar='<region-name>',
            default=env('OS_REGION_NAME'),
            help='Defaults to env[OS_REGION_NAME]')

        parser.add_argument('--os_identity_api_version',
            metavar='<identity-api-version>',
            default=env('OS_IDENTITY_API_VERSION', 'KEYSTONE_VERSION'),
            help='Defaults to env[OS_IDENTITY_API_VERSION] or 2.0')

        parser.add_argument('--token', metavar='<service-token>',
            default=env('SERVICE_TOKEN'),
            help='Defaults to env[SERVICE_TOKEN]')

        parser.add_argument('--endpoint', metavar='<service-endpoint>',
            default=env('SERVICE_ENDPOINT'),
            help='Defaults to env[SERVICE_ENDPOINT]')

        # FIXME(dtroyer): The args below are here for diablo compatibility,
        #                 remove them in folsum cycle

        parser.add_argument('--username', metavar='<auth-user-name>',
            help='Deprecated')

        parser.add_argument('--password', metavar='<auth-password>',
            help='Deprecated')

        parser.add_argument('--tenant_name', metavar='<tenant-name>',
            help='Deprecated')

        parser.add_argument('--auth_url', metavar='<auth-url>',
            help='Deprecated')

        parser.add_argument('--region_name', metavar='<region-name>',
            help='Deprecated')

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_module = {
                '2.0': shell_v2_0,
            }[version]
        except KeyError:
            actions_module = shell_v2_0

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, shell_generic)
        self._find_actions(subparsers, self)

        return parser

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(command,
                help=help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter
            )
            subparser.add_argument('-h', '--help',
                action='help',
                help=argparse.SUPPRESS,
            )
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def main(self, argv):
        # Parse args once to find version
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)

        # build available subcommands based on version
        api_version = options.os_identity_api_version
        subcommand_parser = self.get_subcommand_parser(api_version)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if not argv or options.help:
            self.do_help(options)
            return 0

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Deal with global arguments
        if args.debug:
            httplib2.debuglevel = 1

        # Short-circuit and deal with help command right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0

        #FIXME(usrleon): Here should be restrict for project id same as
        # for username or apikey but for compatibility it is not.

        # provide support for legacy args
        args.os_username = args.os_username or args.username
        args.os_password = args.os_password or args.password
        args.os_auth_url = args.os_auth_url or args.auth_url
        args.os_tenant_name = args.os_tenant_name or args.tenant_name
        args.os_region_name = args.os_region_name or args.region_name

        if not utils.isunauthenticated(args.func):
            # if the user hasn't provided any auth data
            if not (args.token or args.endpoint or args.os_username or
                    args.os_password or args.os_auth_url):
                raise exc.CommandError('Expecting authentication method via \n'
                                       '  either a service token, '
                                       '--token or env[SERVICE_TOKEN], \n'
                                       '  or credentials, '
                                       '--os_username or env[OS_USERNAME].')

            # if it looks like the user wants to provide a service token
            # but is missing something
            if args.token or args.endpoint and not (
                    args.token and args.endpoint):
                if not args.token:
                    raise exc.CommandError('Expecting a token provided '
                            'via either --token or env[SERVICE_TOKEN]')

                if not args.endpoint:
                    raise exc.CommandError('Expecting an endpoint provided '
                            'via either --endpoint or env[SERVICE_ENDPOINT]')

            # if it looks like the user wants to provide a credentials
            # but is missing something
            if ((args.os_username or args.os_password or args.os_auth_url)
                    and not (args.os_username and args.os_password and
                             args.os_auth_url)):
                if not args.os_username:
                    raise exc.CommandError('Expecting a username provided '
                            'via either --os_username or env[OS_USERNAME]')

                if not args.os_password:
                    raise exc.CommandError('Expecting a password provided '
                            'via either --os_password or env[OS_PASSWORD]')

                if not args.os_auth_url:
                    raise exc.CommandError('Expecting an auth URL '
                            'via either --os_auth_url or env[OS_AUTH_URL]')

        if utils.isunauthenticated(args.func):
            self.cs = shell_generic.CLIENT_CLASS(endpoint=args.os_auth_url)
        else:
            token = None
            endpoint = None
            if args.token and args.endpoint:
                token = args.token
                endpoint = args.endpoint
            api_version = options.os_identity_api_version
            self.cs = self.get_api_class(api_version)(
                username=args.os_username,
                tenant_name=args.os_tenant_name,
                tenant_id=args.os_tenant_id,
                token=token,
                endpoint=endpoint,
                password=args.os_password,
                auth_url=args.os_auth_url,
                region_name=args.os_region_name)

        try:
            args.func(self.cs, args)
        except exc.Unauthorized:
            raise exc.CommandError("Invalid OpenStack Identity credentials.")
        except exc.AuthorizationFailure:
            raise exc.CommandError("Unable to authorize user")

    def get_api_class(self, version):
        try:
            return {
                "2.0": shell_v2_0.CLIENT_CLASS,
            }[version]
        except KeyError:
            return shell_v2_0.CLIENT_CLASS

    @utils.arg('command', metavar='<subcommand>', nargs='?',
                          help='Display help for <subcommand>')
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        OpenStackIdentityShell().main(sys.argv[1:])

    except Exception, e:
        if httplib2.debuglevel == 1:
            raise  # dump stack.
        else:
            print >> sys.stderr, e
        sys.exit(1)
