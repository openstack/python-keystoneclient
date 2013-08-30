# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import getpass
import hashlib
import sys

import prettytable

from keystoneclient import exceptions


# Decorator for cli-args
def arg(*args, **kwargs):
    def _decorator(func):
        # Because of the sematics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def print_list(objs, fields, formatters={}, order_by=None):
    pt = prettytable.PrettyTable([f for f in fields],
                                 caching=False, print_empty=False)
    pt.aligns = ['l' for f in fields]

    for o in objs:
        row = []
        for field in fields:
            if field in formatters:
                row.append(formatters[field](o))
            else:
                field_name = field.lower().replace(' ', '_')
                data = getattr(o, field_name, '')
                if data is None:
                    data = ''
                row.append(data)
        pt.add_row(row)

    if order_by is None:
        order_by = fields[0]
    print(pt.get_string(sortby=order_by))


def _word_wrap(string, max_length=0):
    """wrap long strings to be no longer then max_length."""
    if max_length <= 0:
        return string
    return '\n'.join([string[i:i + max_length] for i in
                     range(0, len(string), max_length)])


def print_dict(d, wrap=0):
    """pretty table prints dictionaries.

    Wrap values to max_length wrap if wrap>0
    """
    pt = prettytable.PrettyTable(['Property', 'Value'],
                                 caching=False, print_empty=False)
    pt.aligns = ['l', 'l']
    for (prop, value) in d.iteritems():
        if value is None:
            value = ''
        value = _word_wrap(value, max_length=wrap)
        pt.add_row([prop, value])
    print(pt.get_string(sortby='Property'))


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id
    try:
        if isinstance(name_or_id, int) or name_or_id.isdigit():
            return manager.get(int(name_or_id))
    except exceptions.NotFound:
        pass

    # now try the entity as a string
    try:
        return manager.get(name_or_id)
    except (exceptions.NotFound):
        pass

    # finally try to find entity by name
    try:
        return manager.find(name=name_or_id)
    except exceptions.NotFound:
        msg = ("No %s with a name or ID of '%s' exists." %
               (manager.resource_class.__name__.lower(), name_or_id))
        raise exceptions.CommandError(msg)
    except exceptions.NoUniqueMatch:
        msg = ("Multiple %s matches found for '%s', use an ID to be more"
               " specific." % (manager.resource_class.__name__.lower(),
                               name_or_id))
        raise exceptions.CommandError(msg)


def unauthenticated(f):
    """Adds 'unauthenticated' attribute to decorated function.

    Usage::

        @unauthenticated
        def mymethod(f):
            ...
    """
    f.unauthenticated = True
    return f


def isunauthenticated(f):
    """Checks to see if the function is marked as not requiring authentication
    with the @unauthenticated decorator.

    Returns True if decorator is set to True, False otherwise.
    """
    return getattr(f, 'unauthenticated', False)


def string_to_bool(arg):
    if isinstance(arg, bool):
        return arg

    return arg.strip().lower() in ('t', 'true', 'yes', '1')


def hash_signed_token(signed_text):
    hash_ = hashlib.md5()
    hash_.update(signed_text)
    return hash_.hexdigest()


def prompt_for_password():
    """Prompt user for password if not provided so the password
    doesn't show up in the bash history.
    """
    if not (hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()):
        # nothing to do
        return

    while True:
        try:
            new_passwd = getpass.getpass('New Password: ')
            rep_passwd = getpass.getpass('Repeat New Password: ')
            if new_passwd == rep_passwd:
                return new_passwd
        except EOFError:
            return
