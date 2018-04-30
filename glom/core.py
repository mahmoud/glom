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

import sys
import pdb
import operator
from abc import ABCMeta
from collections import OrderedDict


PY2 = (sys.version_info[0] == 2)
if PY2:
    _AbstractIterableBase = object
else:
    basestring = str
    _AbstractIterableBase = ABCMeta('_AbstractIterableBase', (object,), {})

_MISSING = object()
OMIT = object()

class GlomError(Exception):
    """A base exception for all the errors that might be raised from glom
    logic. By default, exceptions raised from within functions passed
    to glom will not be wrapped in a GlomError.
    """
    pass


class PathAccessError(AttributeError, KeyError, IndexError, GlomError):
    """An amalgamation of KeyError, IndexError, and TypeError,
    representing what can occur when looking up a path in a nested
    object.
    """
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


class CoalesceError(GlomError):
    def __init__(self, coal_obj, skipped, path):
        self.coal_obj = coal_obj
        self.skipped = skipped
        self.path = path

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.coal_obj, self.skipped, self.path)

    def __str__(self):
        missed_specs = tuple(self.coal_obj.sub_specs)
        skipped_vals = [v.__class__.__name__
                        if isinstance(v, self.coal_obj.skip_exc)
                        else '<skipped %s>' % v.__class__.__name__
                        for v in self.skipped]
        msg = ('no valid values found while coalescing. Tried %r and got (%s)'
               % (missed_specs, ', '.join(skipped_vals)))
        if self.coal_obj.skip is not _MISSING:
            msg += ', skip set to %r' % (self.coal_obj.skip,)
        if self.coal_obj.skip_exc is not GlomError:
            msg += ', skip_exc set to %r' % (self.coal_obj.skip_exc,)
        if self.path is not None:
            msg += ' (at path %r)' % (self.path,)

        return msg


class UnregisteredTarget(GlomError):
    def __init__(self, op, target_type, type_map, path):
        self.op = op
        self.target_type = target_type
        self.type_map = type_map
        self.path = path

    def __repr__(self):
        cn = self.__class__.__name__
        return ('%s(%r, %r, %r, %r)'
                % (cn, self.op, self.target_type, self.type_map, self.path))

    def __str__(self):
        if not self.type_map:
            return ("glom() called without registering any types. see glom.register()"
                    " or Glommer's constructor for details.")

        reg_types = sorted([t.__name__ for t, h in self.type_map.items()
                            if getattr(h, self.op, None)])
        reg_types_str = '()' if not reg_types else ('(%s)' % ', '.join(reg_types))
        msg = ("target type %r not registered for '%s', expected one of"
               " registered types: %s" % (self.target_type.__name__, self.op, reg_types_str))
        if self.path:
            msg += ' (at %r)' % (self.path,)

        return msg


class TargetHandler(object):
    def __init__(self, type_obj, get=None, iterate=None):
        self.type = type_obj

        if iterate is None:
            if callable(getattr(type_obj, '__iter__', None)):
                iterate = iter
            else:
                iterate = False
        if iterate is not False and not callable(iterate):
            raise ValueError('expected iterable type or callable for iterate, not: %r'
                             % iterate)
        self.iterate = iterate

        if get is None:
            get = getattr
        if get is not False and not callable(get):
            raise ValueError('expected callable for get, not: %r' % (get,))
        self.get = get


class Path(object):
    """Used to represent explicit paths when the default 'a.b.c'-style
    syntax won't work or isn't desirable.

    Use this to wrap ints, datetimes, and other valid keys, as well as
    strings with dots that shouldn't be expanded.

    >>> target = {'a': {'b': 'c', 'd.e': 'f', 2: 3}}
    >>> glom(target, Path('a', 2))
    3
    >>> glom(target, Path('a', 'd.e'))
    'f'
    """
    def __init__(self, *path_parts):
        self.path_parts = path_parts

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%s)' % (cn, ', '.join([repr(p) for p in self.path_parts]))


class Literal(object):
    """Used to represent a literal value in a spec. Wherever a Literal
    object is encountered in a spec, it is replaced with its *value*
    in the output.

    This could also be achieved with a callable, e.g., `lambda _:
    'literal'` in the spec, but using a Literal object adds some
    explicitness and clarity.
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r)' % (cn, self.value)


class Coalesce(object):
    def __init__(self, *sub_specs, **kwargs):
        self.sub_specs = sub_specs
        self.default = kwargs.pop('default', _MISSING)
        self.skip = kwargs.pop('skip', _MISSING)
        if self.skip is _MISSING:
            self.skip_func = lambda v: False
        elif callable(self.skip):
            self.skip_func = self.skip
        elif isinstance(self.skip, tuple):
            self.skip_func = lambda v: v in self.skip
        else:
            self.skip_func = lambda v: v == self.skip

        self.skip_exc = kwargs.pop('skip_exc', GlomError)
        if kwargs:
            raise TypeError('unexpected keyword args: %r' % (sorted(kwargs.keys()),))


class Inspect(object):
    """Can be used two ways, one as a wrapper around a spec (passed a
    positional argument), or two, as a posarg-less placeholder in a
    tuple.
    """
    def __init__(self, *a, **kw):
        self.wrapped = a[0] if a else Path()
        self.recursive = kw.pop('recursive', False)
        self.echo = kw.pop('echo', True)

        breakpoint = kw.pop('breakpoint', False)
        if breakpoint is True:
            breakpoint = pdb.set_trace
        if breakpoint and not callable(breakpoint):
            raise TypeError('breakpoint expected bool or callable, not: %r' % breakpoint)
        self.breakpoint = breakpoint

        post_mortem = kw.pop('post_mortem', False)
        if post_mortem is True:
            post_mortem = pdb.post_mortem
        if post_mortem and not callable(post_mortem):
            raise TypeError('post_mortem expected bool or callable, not: %r' % post_mortem)
        self.post_mortem = post_mortem

    def __repr__(self):
        return '<INSPECT>'


class _AbstractIterable(_AbstractIterableBase):
    __metaclass__ = ABCMeta

    @classmethod
    def __subclasshook__(cls, C):
        if cls is _AbstractIterable:
            if C in (str, bytes):
                return False
            return callable(getattr(C, "__iter__", None))
        return NotImplemented


class Glommer(object):
    """All the wholesome goodness that it takes to make glom work. This
    type mostly serves to encapsulate the type registration context so
    that advanced uses of glom don't need to worry about stepping on
    each other's toes.
    """
    def __init__(self, register_default_types=True):
        self._type_map = OrderedDict()
        self._type_tree = OrderedDict()  # see _register_fuzzy_type for details

        if register_default_types:
            self._register_default_types()

        self._unreg_handler = TargetHandler(None, get=False, iterate=False)

        return

    def _get_handler(self, obj):
        "return the closest-matching type config for an object *instance*, obj"
        try:
            return self._type_map[type(obj)]
        except KeyError:
            pass
        closest = self._get_closest_type(obj)
        if closest is None:
            return self._unreg_handler
        return self._type_map[closest]

    def _get_closest_type(self, obj, _type_tree=None):
        type_tree = _type_tree if _type_tree is not None else self._type_tree
        default = None
        for cur_type, sub_tree in type_tree.items():
            if isinstance(obj, cur_type):
                sub_type = self._get_closest_type(obj, _type_tree=sub_tree)
                ret = cur_type if sub_type is None else sub_type
                return ret
        return default

    def _register_default_types(self):
        self.register(object)
        self.register(dict, operator.getitem)
        self.register(list, operator.getitem)
        self.register(tuple, operator.getitem)
        self.register(_AbstractIterable, iterate=iter)

    def _register_fuzzy_type(self, new_type, _type_tree=None):
        """Build a "type tree", an OrderedDict mapping registered types to
        their subtypes

        The type tree's invariant is that a key in the mapping is a
        valid parent type of all its children.

        Order is preserved such that non-overlapping parts of the
        subtree take precedence by which was most recently added.
        """
        type_tree = _type_tree if _type_tree is not None else self._type_tree

        registered = False
        for cur_type, sub_tree in list(type_tree.items()):
            if issubclass(cur_type, new_type):
                sub_tree = type_tree.pop(cur_type)  # mutation for recursion brevity
                try:
                    type_tree[new_type][cur_type] = sub_tree
                except KeyError:
                    type_tree[new_type] = OrderedDict({cur_type: sub_tree})
                registered = True
            elif issubclass(new_type, cur_type):
                type_tree[cur_type] = self._register_fuzzy_type(new_type, _type_tree=sub_tree)
                registered = True

        if not registered:
            type_tree[new_type] = OrderedDict()

        return type_tree

    def register(self, target_type, get=None, iterate=None, exact=False):
        """Register a new type with the Glommer so it will know how to handle
        it as a target.
        """
        if not isinstance(target_type, type):
            raise TypeError('register expected a type, not an instance: %r' % (target_type,))
        self._type_map[target_type] = TargetHandler(target_type, get=get, iterate=iterate)
        if not exact:
            self._register_fuzzy_type(target_type)
        return

    def _get_path(self, target, path):
        try:
            parts = path.split('.')
        except (AttributeError, TypeError):
            parts = getattr(path, 'path_parts', None)
            if parts is None:
                raise TypeError('path expected str or Path object, not: %r' % path)

        cur, val = target, target
        for i, part in enumerate(parts):
            handler = self._get_handler(cur)
            if not handler.get:
                raise UnregisteredTarget('get', type(target), self._type_map, path=path[:i])
            try:
                val = handler.get(cur, part)
            except Exception as e:
                raise PathAccessError(e, part, parts)
            cur = val
        return val

    def glom(self, target, spec, **kwargs):
        # TODO: check spec up front
        # TODO: default
        # TODO: de-recursivize this
        # TODO: rearrange the branching below by frequency of use

        # self.glom() calls should pass path=path to elide the current
        # step, otherwise add themselves in some fashion.
        path = kwargs.pop('_path', [])
        inspector = kwargs.pop('_inspect', None)
        next_inspector = inspector if (inspector and inspector.recursive) else None
        if inspector:
            if inspector.echo:
                print()
                print('path:  ', path + [spec])
                print('target:', target)
            if inspector.breakpoint:
                inspector.breakpoint()

        if isinstance(spec, Inspect):
            try:
                ret = self.glom(target, spec.wrapped, _path=path, _inspect=spec)
            except Exception:
                if spec.post_mortem:
                    spec.post_mortem()
                raise
        elif isinstance(spec, dict):
            ret = type(spec)() # TODO: works for dict + ordereddict, but sufficient for all?

            for field, sub_spec in spec.items():
                val = self.glom(target, sub_spec, _path=path, _inspect=next_inspector)
                if val is OMIT:
                    continue
                ret[field] = val
        elif isinstance(spec, list):
            sub_spec = spec[0]
            handler = self._get_handler(target)
            if not handler.iterate:
                raise UnregisteredTarget('iterate', type(target), self._type_map, path=path)

            try:
                iterator = handler.iterate(target)
            except TypeError as te:
                raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                                % (target.__class__.__name__, Path(*path), te))
            ret = []
            for i, t in enumerate(iterator):
                val = self.glom(t, sub_spec, _path=path + [i])
                if val is OMIT:
                    continue
                ret.append(val)
        elif isinstance(spec, tuple):
            res = target
            for sub_spec in spec:
                res = self.glom(res, sub_spec, _path=path, _inspect=next_inspector)
                next_inspector = sub_spec if (isinstance(sub_spec, Inspect) and sub_spec.recursive) else next_inspector
                if not isinstance(sub_spec, list):
                    path = path + [getattr(sub_spec, '__name__', sub_spec)]
            ret = res
        elif callable(spec):
            ret = spec(target)
        elif isinstance(spec, (basestring, Path)):
            try:
                ret = self._get_path(target, spec)
            except PathAccessError as pae:
                pae.path = Path(*(path + list(pae.path)))
                raise
        elif isinstance(spec, Coalesce):
            skipped = []
            for sub_spec in spec.sub_specs:
                try:
                    ret = self.glom(target, sub_spec, _path=path, _inspect=next_inspector)
                    if not spec.skip_func(ret):
                        break
                    skipped.append(ret)
                except spec.skip_exc as e:
                    skipped.append(e)
                    continue
            else:
                if spec.default is not _MISSING:
                    ret = spec.default
                else:
                    raise CoalesceError(spec, skipped, path)
        elif isinstance(spec, Literal):
            ret = spec.value
        else:
            raise TypeError('expected spec to be dict, list, tuple,'
                            ' callable, or string, not: %r' % spec)
        if inspector and inspector.echo:
            print('output:', ret)
            print()

        return ret


_DEFAULT = Glommer(register_default_types=True)
glom = _DEFAULT.glom
register = _DEFAULT.register


def _main():
    pass  # TODO: take a json and a spec (flag for safe eval vs non-safe eval)


if __name__ == '__main__':
    _main()

"""TODO:

* Add extra top-level coalesce for default behavior
* More subspecs
  * Inspect
  * Call() - Call(func) for kwargs into function, Call.method for kwargs into method
  * Target() - Do anything Target[1].method(), etc.

(Call and Target have better aesthetics and repr compared to lambdas, but are otherwise no more capable)

* More supported target types
  * Django and SQLAlchemy Models and QuerySets

## Django models registration:

glom.register(django.db.models.Manager, iterate=lambda m: m.all())
glom.register(django.db.models.QuerySet, iterate=lambda qs: qs.all())



* Support unregistering target types
* Eventually: Support registering handlers for new spec types in the
  main glom function. allows users to handle types beyond the glom
  builtins. Will require really defining the function interface for
  what a glom takes; currently: target, spec, _path, _inspect.
* What to do with empty list and empty tuple (in spec)?
* Flag (and exception type) to gather all errors, instead of raising
  the first
* Contact example

glom(contact, {
    'name': 'name',  # simple get-attr
    'primary_email': 'primary_email.email',  # multi-level get-attr
    'emails': ('email_set', ['email']),  # get-attr + sequence unpack + fetch one attr
    'roles': ('vendor_roles', [{'role': 'role'}]),  # get-attr + sequence unpack + sub-glom
})

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
