"""
This module contains Specs that perform mutations.
"""
import operator
from pprint import pprint

from .core import Path, T, S, Spec, glom, UnregisteredTarget
from .core import TType, register_op, TargetRegistry

try:
    basestring
except NameError:
    basestring = str


if getattr(__builtins__, '__dict__', None):
    # pypy's __builtins__ is a module, as is CPython's REPL, but at
    # normal execution time it's a dict?
    __builtins__ = __builtins__.__dict__


class Assign(object):
    """The Assign specifier type enables glom to modify the target,
    performing a "deep-set" to mirror glom's original deep-get use
    case.

    Assign can be used to perform spot modifications of large data
    structures when making a copy is not desirable.

    >>> target = {'a': {}}
    >>> spec = Assign('a.b', 'value')
    >>> _ = glom(target, spec)
    >>> pprint(target)
    {'a': {'b': 'value'}}

    The value to be assigned can also be a Spec, which is useful for
    copying values around within the data structure.

    >>> _ = glom(target, Assign('a.c', Spec('a.b')))
    >>> pprint(target)
    {'a': {'b': 'value', 'c': 'value'}}

    The target path can be a :data:`~glom.T` expression, for maximum control:

    >>> err = ValueError('initial message')
    >>> target = {'errors': [err]}
    >>> _ = glom(target, Assign(T['errors'][0].args, ('new message',)))
    >>> str(err)
    'new message'

    """
    def __init__(self, path, val):
        # TODO: an option like require_preexisting or something to
        # ensure that a value is mutated, not just added. Current
        # workaround is to do a Check().
        if isinstance(path, basestring):
            path = Path.from_text(path)
        elif type(path) is TType:
            path = Path(path)
        elif not isinstance(path, Path):
            raise TypeError('path argument must be a .-delimited string, Path, T, or S')

        try:
            self.op, self.arg = path.items()[-1]
        except IndexError:
            raise ValueError('path must have at least one element')
        self.path = path[:-1]

        if self.op not in '[.P':
            # maybe if we add null-coalescing this should do something?
            raise ValueError('last part of path must be setattr or setitem')
        self.val = val

    def glomit(self, target, scope):
        if type(self.val) is Spec:
            val = scope[glom](target, self.val, scope)
        else:
            val = self.val
        dest = scope[glom](target, self.path, scope)
        # TODO: forward-detect immutable dest?
        if self.op == '[':
            dest[self.arg] = val
        elif self.op == '.':
            setattr(dest, self.arg, val)
        elif self.op == 'P':
            assign = scope[TargetRegistry].get_handler('assign', dest)
            if not assign:
                raise UnregisteredTarget('assign', type(dest),
                                         scope[TargetRegistry].get_type_map('assign'),
                                         path=scope[Path])
            try:
                assign(dest, self.arg, val)
            except Exception as e:
                # should be a GlomError
                raise TypeError('failed to assign on instance of type %r at %r (got %r)'
                                % (dest.__class__.__name__, Path(*scope[Path]), e))

        return target


def assign(obj, path, val):
    return glom(obj, Assign(path, val))


_ALL_BUILTIN_TYPES = [v for v in __builtins__.values() if isinstance(v, type)]
_BUILTIN_BASE_TYPES = [v for v in _ALL_BUILTIN_TYPES
                       if not issubclass(v, tuple([t for t in _ALL_BUILTIN_TYPES
                                                   if t not in (v, type, object)]))]
_UNASSIGNABLE_BASE_TYPES = tuple(set(_BUILTIN_BASE_TYPES)
                                 - set([dict, list, BaseException, object, type]))


def _set_sequence_item(target, idx, val):
    target[int(idx)] = val


def _assign_autodiscover(type_obj):
    # TODO: issubclass or "in"?
    if issubclass(type_obj, _UNASSIGNABLE_BASE_TYPES):
        return False

    if callable(getattr(type_obj, '__setitem__', None)):
        if callable(getattr(type_obj, 'index', None)):
            return _set_sequence_item
        return operator.setitem

    return setattr


register_op('assign', auto_func=_assign_autodiscover, exact=False)
