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

from __future__ import print_function

class Path(object):
    """Used to represent explicit paths when the default 'a.b.c'-style
    syntax won't work or isn't desirable.

    Use this to wrap ints, datetimes, and other valid keys, as well as
    strings with dots that shouldn't be expanded.

    >>> target = {'a': {'b': 'c', 'd.e': 'f', 2: 3}}
    >>> glom(target, {'a_d': Path('a', 'd.e'), 'a_2': Path('a', 2)})
    {'a_de': 'f', 'a_2': 3}
    """
    def __init__(self, *path_parts):
        self.path_parts = path_parts


class Glommer(object):
    def __init__(self):
        self._map = {}
        self._list = []

    def register(self, target_type, getter, iterate=False):
        '''
        register a new type with the Glommer so it will know
        how to handle it as a target
        '''
        # should maybe also take return type
        if iterate is True:
            iterate = iter
        if iterate is not False and not callable(iterate):
            raise ValueError('iterate must be iteration function or True')
        if not callable(getter):
            raise ValueError('getter must be get attribute function')
        self._map[target_type] = (getter, iterate)
        self._list.append((getter, iterate))
        return

    def _get_path(self, target, path):
        try:
            parts = path.split('.')
        except (AttributeError, TypeError):
            parts = getattr(path, 'path_parts', None)
            if parts is None:
                raise TypeError('path expected str or Path object, not: %r' % path)
        # TODO: is it ok to return None here as a default when path is empty?
        cur, val = target, None
        for part in parts:
            getter = self._map[type(cur)][0]
            val = getter(cur, part)
            cur = val
        return val

    def glom(self, target, spec):
        # TODO: good error
        # TODO: default
        # TODO: de-recursivize this
        if isinstance(spec, dict):
            ret = {}  # TODO: configurable based on registered type
            for field, sub_spec in spec.items():
                ret[field] = glom(target, sub_spec)
            return ret
        elif isinstance(spec, list):
            sub_spec = spec[0]
            iterator = self._map[type(target)][1](target)
            return [glom(t, sub_spec) for t in iterator]
        elif isinstance(spec, tuple):
            res = target
            for sub_spec in spec:
                res = glom(res, sub_spec)
            return res
        elif callable(spec):
            return spec(target)
        elif isinstance(spec, (basestring, Path)):
            return self._get_path(target, spec)
        raise TypeError('expected spec to be dict, list, tuple,'
                        ' callable, or string, not: %r' % spec)
        return


_DEFAULT = Glommer()
glom = _DEFAULT.glom


_DEFAULT.register(object, object.__getattribute__)
_DEFAULT.register(dict, dict.__getitem__)
_DEFAULT.register(list, list.__getitem__, True)  # TODO: are iterate and getter mutually exclusive or?


def _main():
    val = {'a': {'b': 'c'},
           'd': {'e': ['f'],
                 'g': 'h'},
           'i': [{'j': 'k', 'l': 'm'}],
           'n': 'o'}

    ret = glom(val, {'a': 'a.b',
                     'e': 'd.e',
                     'i': ('i', [{'j': 'j'}]),  # TODO: support True for cases when the value should simply be mapped into the field name?
                     'n': ('n', lambda n: n.upper())})  # d.e[0] or d.e: (callable to fetch 0)

    print('in: ', val)
    print('got:', ret)
    expected = {'a': 'c',
                'e': ['f'],
                'i': [{'j': 'k'}],
                'n': 'O'}
    print('exp:', expected)

    print(glom(range(10), Path(1)))  # test list getting and Path
    return


if __name__ == '__main__':
    _main()

"""TODO:

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

---

Need to raise a good exception on failure to fetch. Maybe:

class PathAccessError(KeyError, IndexError, TypeError):
    '''An amalgamation of KeyError, IndexError, and TypeError,
    representing what can occur when looking up a path in a nested
    object.
    '''
    def __init__(self, exc, seg, path):
        self.exc = exc
        self.seg = seg
        self.path = path

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.exc, self.seg, self.path)

    def __str__(self):
        return ('could not access %r from path %r, got error: %r'
                % (self.seg, self.path, self.exc))


Also need the ability to specify defaults if something is not found,
as opposed to raising an error. Default varies by whether or not to
iterate. Empty list if yes, None if no.

"""
