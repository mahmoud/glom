"""*glom gets results.*

To be more precise, glom helps pull together objects from other
objects in a declarative, dynamic, and downright simple way.

Built with services, APIs, and general serialization in mind, glom
helps filter objects as well as perform deep fetches which would be
tedious to perform in a procedural manner.

Where "schema" and other libraries focus on validation and parsing
less-structured data into Python objects, glom goes the other
direction, producing more-readily serializable data from valid
higher-level objects.

"""

_REGISTRY_MAP = {}
_REGISTRY_LIST = []  # TODO or some sort of tree


def register(target_type, getter, iterate=False):
    if iterate is True:
        iterate = iter
    if iterate is not False and not callable(iterate):
        raise ValueError()

    if not callable(getter):
        raise ValueError()

    _REGISTRY_MAP[target_type] = (getter, iterate)
    _REGISTRY_LIST.append((getter, iterate))

    return


def _get_path(target, path):
    parts = path.split('.')
    cur, val = target, None
    for part in parts:
        getter = _REGISTRY_MAP[type(cur)][0]
        val = getter(cur, part)
        cur = val
    return val


def glom(target, spec, ret=None):
    ret = {} if ret is None else ret

    for field, sub in spec.items():
        if isinstance(sub, str):
            cur_src = sub
            processor = None
        elif isinstance(sub, tuple):
            cur_src = sub[0]
            processor = sub[1]
        else:
            raise ValueError('expected string path, or tuple of (string path, processor), not: %r' % sub)

        iterate = False
        if isinstance(processor, list):
            iterate = True
            processor = processor[0]
            if isinstance(processor, str):
                processor = lambda v, p=processor: _get_path(v, p)

        if iterate:
            value = [processor(val) if processor else val
                     for val in _get_path(target, cur_src)]
            print 'iterated', value
        else:
            val = _get_path(target, cur_src)
            value = processor(val) if processor else val

        ret[field] = value

    return ret


# TODO: is it really necessary to register a "get_fields"
register(object, object.__getattribute__)
register(dict, dict.__getitem__)
register(list, list.__getitem__, True)  # TODO: are iterate and getter mutually exclusive or?


def _main():
    val = {'a': {'b': 'c'},
           'd': {'e': ['f'],
                 'g': 'h'},
           'i': [{'j': 'k', 'l': 'm'}],
           'n': 'o'}

    ret = glom(val, {'a': 'a.b',
                     'e': 'd.e',
                     'i': ('i', ['j']),
                     'n': ('n', lambda n: n.upper())})  # d.e[0] or d.e: (callable to fetch 0)

    print('in: ', val)
    print('got:', ret)
    expected = {'a': 'c',
                'e': ['f'],
                'i': ['k'],
                'n': 'O'}
    print('exp:', expected)
    return


if __name__ == '__main__':
    _main()

"""
TODO:

* More subspecs
  * dicts
  * lists (indicating iterability)
  * callables (for advanced processing)
* More supported target types
  * Django and SQLAlchemy Models and QuerySets
* Support for subclasses/superclasses via type tree


idealized API (from the whiteboard with slight translation)

glom({
    'name': 'name',  # simple get-attr
    'primary_email': 'primary_email.email',  # multi-level get-attr
    'emails': ('email_set', ['email']),  # get-attr + sequence unpack + fetch one attr
    'roles': ('vendor_roles', [{'role': 'role'}]),  # get-attr + sequence unpack + sub-glom
}, contact)

ideas from this:
every value of the dict is moving down a level, the algorithm is to repeatedly
walk down levels via get-attr + sequence unpacks until you run out of levels
and then whatever you have arrived at goes in that spot

you could also maybe glom to a list by just taking the values() of the above dict
glom([
   'name', 'primary_email.email', ('email_set', ['email']), ('vendor_roles', [{'role': 'role'}])
], contact)

would be cool to have glom gracefully degrade to a get_path:

  glob({'a': {'b': 'c'}}, 'a.b') -> 'c'

(spec is just a string instead of a dict, target is still a dict obvs)

"""
