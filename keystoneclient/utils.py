import uuid
import hashlib

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

def convert(input):
    if isinstance(input, dict):
        ret = {}
        for key in input:
            key = key.encode('ascii')
            ret[key] = convert(input.get(key))
    elif isinstance(input, list):
        ret = []
        for i in range(len(input)):
            ret.append(convert(input[i]))
    else:
        ret = input.encode('ascii')
    return ret


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def print_list(objs, fields, formatters={}, order_by=None):
    pt = prettytable.PrettyTable([f for f in fields], caching=False)
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
    print pt.get_string(sortby=order_by)


def _word_wrap(string, max_length=0):
    """wrap long strings to be no longer then max_length"""
    if max_length <= 0:
        return string
    return '\n'.join([string[i:i + max_length] for i in
                     range(0, len(string), max_length)])


def print_dict(d, wrap=0):
    """pretty table prints dictionaries.

    Wrap values to max_length wrap if wrap>0
    """
    pt = prettytable.PrettyTable(['Property', 'Value'], caching=False)
    pt.aligns = ['l', 'l']
    for (prop, value) in d.iteritems():
        if value is None:
            value = ''
        value = _word_wrap(str(value), max_length=wrap)
        pt.add_row([prop, value])
    print pt.get_string(sortby='Property')


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id
    try:
        if isinstance(name_or_id, int) or name_or_id.isdigit():
            return manager.get(int(name_or_id))
    except exceptions.NotFound:
        pass

    # now try to get entity as uuid
    try:
        uuid.UUID(str(name_or_id))
        return manager.get(name_or_id)
    except (ValueError, exceptions.NotFound):
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
        raise exc.CommandError(msg)


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
    """
    Checks to see if the function is marked as not requiring authentication
    with the @unauthenticated decorator. Returns True if decorator is
    set to True, False otherwise.
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
