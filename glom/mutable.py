"""
This module contains Specs that perform mutations.
"""
import operator
from pprint import pprint

from .core import Path, T, S, Spec, glom, UnregisteredTarget, GlomError, PathAccessError
from .core import TType, register_op, TargetRegistry

try:
    basestring
except NameError:
    basestring = str


if getattr(__builtins__, '__dict__', None):
    # pypy's __builtins__ is a module, as is CPython's REPL, but at
    # normal execution time it's a dict?
    __builtins__ = __builtins__.__dict__


class PathAssignError(GlomError):
    """This :exc:`GlomError` subtype is raised when an assignment fails,
    stemming from an :func:`~glom.assign` call or other
    :class:`~glom.Assign` usage.

    One example would be assigning to an out-of-range position in a list::

      >>> assign(["short", "list"], Path(5), 'too far')
      Traceback (most recent call last):
      ...
      PathAssignError: could not assign 5 on object at Path(), got error: IndexError(...

    Other assignment failures could be due to assigning to an
    ``@property`` or exception being raised inside a ``__setattr__()``.

    """
    def __init__(self, exc, path, dest_name):
        self.exc = exc
        self.path = path
        self.dest_name = dest_name

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.exc, self.path, self.dest_name)

    def __str__(self):
        return ('could not assign %r on object at %r, got error: %r'
                % (self.dest_name, self.path, self.exc))


class Assign(object):
    """The ``Assign`` specifier type enables glom to modify the target,
    performing a "deep-set" to mirror glom's original deep-get use
    case.

    ``Assign`` can be used to perform spot modifications of large data
    structures when making a copy is not desired::

      # deep assignment into a nested dictionary
      >>> target = {'a': {}}
      >>> spec = Assign('a.b', 'value')
      >>> _ = glom(target, spec)
      >>> pprint(target)
      {'a': {'b': 'value'}}

    The value to be assigned can also be a :class:`~glom.Spec`, which
    is useful for copying values around within the data structure::

      # copying one nested value to another
      >>> _ = glom(target, Assign('a.c', Spec('a.b')))
      >>> pprint(target)
      {'a': {'b': 'value', 'c': 'value'}}

    Like many other specifier types, ``Assign``'s destination path can be
    a :data:`~glom.T` expression, for maximum control::

      # changing the error message of an exception in an error list
      >>> err = ValueError('initial message')
      >>> target = {'errors': [err]}
      >>> _ = glom(target, Assign(T['errors'][0].args, ('new message',)))
      >>> str(err)
      'new message'

    ``Assign`` has built-in support for assigning to attributes of
    objects, keys of mappings (like dicts), and indexes of sequences
    (like lists). Additional types can be registered through
    :func:`~glom.register()` using the ``"assign"`` operation name.

    Attempting to assign to an immutable structure, like a
    :class:`tuple`, will result in a
    :class:`~glom.PathAssignError`. Attempting to assign to a path
    that doesn't exist will raise a :class:`~PathAccessError`.

    To automatically backfill missing structures, you can pass a
    callable to the *missing* argument. This callable will be called
    for each path segment along the assignment which is not
    present.

       >>> target = {}
       >>> assign(target, 'a.b.c', 'hi', missing=dict)
       {'a': {'b': {'c': 'hi'}}}

    """
    def __init__(self, path, val, missing=None):
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
        self._orig_path = path
        self.path = path[:-1]

        if self.op not in '[.P':
            # maybe if we add null-coalescing this should do something?
            raise ValueError('last part of path must be setattr or setitem')
        self.val = val

        if missing is not None:
            if not callable(missing):
                raise TypeError('expected missing to be callable, not %r' % (missing,))
        self.missing = missing

    def glomit(self, target, scope):
        if type(self.val) is Spec:
            val = scope[glom](target, self.val, scope)
        else:
            val = self.val

        op, arg, path = self.op, self.arg, self.path
        if self.path.startswith(S):
            dest_target = scope.parents
            dest_path = self.path.from_t()
        else:
            dest_target = target
            dest_path = self.path
        try:
            dest = scope[glom](dest_target, dest_path, scope)
        except PathAccessError as pae:
            if not self.missing:
                raise

            remaining_path = self._orig_path[pae.part_idx + 1:]
            val = scope[glom](self.missing(), Assign(remaining_path, val, missing=self.missing), scope)

            op, arg = self._orig_path.items()[pae.part_idx]
            path = self._orig_path[:pae.part_idx]
            dest = scope[glom](dest_target, path, scope)

        # TODO: forward-detect immutable dest?
        if op == '[':
            dest[arg] = val
        elif op == '.':
            setattr(dest, arg, val)
        elif op == 'P':
            _assign = scope[TargetRegistry].get_handler('assign', dest)
            if not _assign:
                raise UnregisteredTarget('assign', type(dest),
                                         scope[TargetRegistry].get_type_map('assign'),
                                         path=scope[Path])
            try:
                _assign(dest, arg, val)
            except Exception as e:
                raise PathAssignError(e, path, arg)

        return target


def assign(obj, path, val, missing=None):
    """The ``assign()`` function provides convenient "deep set"
    functionality, modifying nested data structures in-place::

      >>> target = {'a': [{'b': 'c'}, {'d': None}]}
      >>> _ = assign(target, 'a.1.d', 'e')  # let's give 'd' a value of 'e'
      >>> pprint(target)
      {'a': [{'b': 'c'}, {'d': 'e'}]}

    Missing structures can also be automatically created with the
    *missing* parameter. For more information and examples, see the
    :class:`~glom.Assign` specifier type, which this function wraps.
    """
    return glom(obj, Assign(path, val, missing=missing))


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
