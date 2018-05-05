"""*glom gets results.*
To be more precise, glom helps pull together objects from other
objects in a declarative, dynamic, and downright simple way.

Built with services, APIs, and general serialization in mind, glom
helps filter objects, as well as perform deep fetches which would be
tedious to perform in a procedural manner.

Where "schema" and other libraries focus on validation and parsing
less-structured data into Python objects, glom goes the other
direction, producing more-readily serializable data from valid
higher-level objects.
"""

from __future__ import print_function

import sys
import pdb
import weakref
import operator
from abc import ABCMeta
from pprint import pprint
from collections import OrderedDict

from boltons.typeutils import make_sentinel

PY2 = (sys.version_info[0] == 2)
if PY2:
    _AbstractIterableBase = object
else:
    basestring = str
    _AbstractIterableBase = ABCMeta('_AbstractIterableBase', (object,), {})


_MISSING = make_sentinel('_MISSING')
OMIT =  make_sentinel('OMIT')


class GlomError(Exception):
    """The base exception for all the errors that might be raised from
    :func:`glom` processing logic.

    By default, exceptions raised from within functions passed to glom
    (e.g., ``len``, ``sum``, any ``lambda``s) will not be wrapped in a
    GlomError.
    """
    pass


class PathAccessError(AttributeError, KeyError, IndexError, GlomError):
    """An amalgamation of KeyError, IndexError, and TypeError,
    representing what can occur when looking up a path in a nested
    object.
    """
    def __init__(self, exc, path, idx):
        self.exc = exc
        self.path = path
        self.path_idx = idx

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.exc, self.path, self.path_idx)

    def __str__(self):
        return ('could not access %r, part %r in path %r, got error: %r'
                % (self.path[self.path_idx], self.path_idx, self.path, self.exc))


class CoalesceError(GlomError):
    """This :exc:`GlomError` subtype is raised from within a
    :class:`Coalesce` spec's processing, when none of the subspecs
    match and no default is provided.

    The exception object itself keeps track of several values which
    may be useful for processing:

    Args:
       coal_obj (Coalese): The original failing spec, see
          :class:`Coalesce`'s docs for details.
       skipped (list): A list of ignored values and exceptions, in the
          order that their respective subspecs appear in the original
          *coal_obj*.
       path: Like many GlomErrors, this exception knows the path at
          which it occurred.
    """
    def __init__(self, coal_obj, skipped, path):
        self.coal_obj = coal_obj
        self.skipped = skipped
        self.path = path

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.coal_obj, self.skipped, self.path)

    def __str__(self):
        missed_specs = tuple(self.coal_obj.subspecs)
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
    """This :class:`GlomError` subtype is raised when a spec calls for an
    unsupported action on a target type. For instance, trying to
    iterate on an non-iterable target:

    >>> glom(object(), ['a.b.c'])
    Traceback (most recent call last):
    ...
    UnregisteredTarget: target type 'object' not registered for 'iterate', expected one of registered types: (...)

    It should be noted that this is a pretty uncommon occurrence in
    production glom usage. See the "Setup and registration" section
    for details on how to avoid this error.

    An UnregisteredTarget takes and tracks a few values:

    Args:
       op (str): The name of the operation being performed ('get' or 'iterate')
       target_type (type): The type of the target being processed.
       type_map (dict): A mapping of target types that do support this operation
       path: The path at which the error occurred.

    """
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
    """The TargetHandler is a construct used internally to register
    general actions on types of targets. The logic for matching a
    target to its handler based on type is in
    :meth:`Glommer._get_handler()`.

    """
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
    """Path objects are used as specs to represent explicit paths when
    the default 'a.b.c'-style general access syntax won't work or
    isn't desirable.

    Use this to wrap ints, datetimes, and other valid keys, as well as
    strings with dots that shouldn't be expanded.

    >>> target = {'a': {'b': 'c', 'd.e': 'f', 2: 3}}
    >>> glom(target, Path('a', 2))
    3
    >>> glom(target, Path('a', 'd.e'))
    'f'
    """
    def __init__(self, *path_parts):
        self.path_parts = list(path_parts)

    def append(self, part):
        self.path_parts.append(part)

    def __getitem__(self, idx):
        return self.path_parts.__getitem__(idx)

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%s)' % (cn, ', '.join([repr(p) for p in self.path_parts]))


class Literal(object):
    """Literal objects are used as specs to wrap a literal value in
    rare cases when part of the spec should not be interpreted as a
    glommable subspec. Wherever a Literal object is encountered in a
    spec, it is replaced with its *value* in the output.

    Args:
       value: The literal value that should appear in the glom output.

    This could also be achieved with a callable, e.g., `lambda _:
    'literal'` in the spec, but using a Literal object adds some
    explicitness and code clarity.
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r)' % (cn, self.value)


class Spec(object):
    """Spec objects are the complement to Literals, wrapping a value
    and marking that it should be interpreted as a glom spec, rather
    than a literal value in places where it would be interpreted as
    a value by defualt. (Such as T[key], Call(func) where key and
    func are assumed to be literal values and not specs.)

    Args:
        value: The glom spec.
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r)' % (cn, self.value)


class Coalesce(object):
    """Coalesce objects are specs used to achieve fallback behavior for a
    list of subspecs. Each subspec is passed as a positional argument,
    and keyword arguments control the fallback and default behaviors.

    In practice, this fallback behavior is as straightforward as it is useful:

    >>> target = {'c': 'd'}
    >>> glom(target, Coalesce('a', 'b', 'c'))
    'd'

    glom tries to get ``'a'`` from ``target``, but gets a
    KeyError. Rather than raise a :exc:`~glom.core.PathAccessError` as usual,
    glom *coalesces* into the next subspec, ``'b'``. The process
    repeats until it gets to ``'c'``, which returns our value,
    ``'d'``. If our value weren't present, we'd see:

    >>> target = {}
    >>> glom(target, Coalesce('a', 'b'))
    Traceback (most recent call last):
    ...
    CoalesceError: no valid values found while coalescing. Tried ('a', 'b') and got (PathAccessError, PathAccessError) ...

    Same process, but because ``target`` is empty, we get a
    :exc:`CoalesceError`. If we want to avoid an exception, and we
    know which value we want by default, we can set *default*:

    >>> target = {}
    >>> glom(target, Coalesce('a', 'b', 'c'), default='d-fault')
    'd-fault'

    ``'a'``, ``'b'``, and ``'c'`` weren't present so we got ``'d-fault'``.

    Args:

       subspecs: One or more glommable subspecs
       default: A value to return if no subspec results in a valid value
       skip: A value, tuple of values, or predicate function
         representing values to ignore
       skip_exc: An exception or tuple of exception types to catch and
         move on to the next subspec. Defaults to :exc:`GlomError`, the
         parent type of all glom runtime exceptions.

    If all subspecs produce skipped values or exceptions, a
    :exc:`CoalesceError` will be raised.

    """
    def __init__(self, *subspecs, **kwargs):
        self.subspecs = subspecs
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


class Call(object):
    """Specifies when a target should be passed to a function,
    *func*. ``Call`` is similar to :class:`~functools.partial` in that
    it is no more powerful than ``lambda`` or other functions, but
    it is designed to be more readable, with a better ``repr``.
    Args:
       func (callable): a function or other callable to be called with
          the target
    Call also combines well with :class:`Target` to construct
    objects. For instance, to generate a dict and then pass it to a
    constructor:
    >>> class ExampleClass(object):
    ...    def __init__(self, attr):
    ...        self.attr = attr
    ...
    >>> target = {'attr': 3.14}
    >>> glom(target, Call(ExampleClass, kwargs=T)).attr
    3.14

    Which is of course equivalent to is equivalent to ``glom(target,
    lambda target: ExampleClass(**target))``, but it's easy to see
    which one reads better.
    """
    def __init__(self, func, args=None, kwargs=None):
        if not callable(func):
            raise TypeError('Call constructor expected func to be a callable,'
                            ' not: %r' % func)
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        if not (callable(func) or isinstance(func, _TType)):
            raise TypeError('func must be a callable or child of T')
        self.func, self.args, self.kwargs = func, args, kwargs

    def __call__(self, target, path, inspector, recurse):
        'run against the current target'
        def eval(t):
            if type(t) in (Spec, _TType):
                return recurse(target, t, path, inspector)
            return t
        if type(self.args) is _TType:
            args = eval(self.args)
        else:
            args = [eval(a) for a in self.args]
        if type(self.kwargs) is _TType:
            kwargs = eval(self.kwargs)
        else:
            kwargs = {name: eval(val) for name, val in self.kwargs.items()}
        return eval(self.func)(*args, **kwargs)


    def __repr__(self):
        return 'Call(%r, args=%r, kwargs=%r)' % (self.func, self.args, self.kwargs)


class _TType(object):
    """Represents the current target, for deferred operations.
    Most operations that can be overloaded can be applied to the
    T instance rather than using a lambda.
    e.g. (lambda t: t.field[5]) could be written (T.field[5])
    """
    __slots__ = ('__weakref__',)

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError('T instances reserve dunder attributes')
        return _t_child(self, '.', name)

    def __getitem__(self, item):
        if item is UP:
            newpath = _T_PATHS[self][:-2]
            if not newpath:
                return T
            t = _TType()
            _T_PATHS[t] = _T_PATHS[self][:-2]
            return t
        return _t_child(self, '[', item)

    def __call__(self, *args, **kwargs):
        return _t_child(self, '(', (args, kwargs))

    def __repr__(self):
        return "T" + _path_fmt(_T_PATHS[self])


_T_PATHS = weakref.WeakKeyDictionary()


def _t_child(parent, operation, arg):
    t = _TType()
    _T_PATHS[t] = _T_PATHS[parent] + (operation, arg)
    return t


# TODO: merge _t_eval with Path access somewhat and remove these exceptions.
# T should be a valid path segment, we just need to keep path/path_idx up to date on the PAE
class GlomAttributeError(GlomError, AttributeError): pass
class GlomKeyError(GlomError, KeyError): pass
class GlomIndexError(GlomError, IndexError): pass


def _path_fmt(path):
    def kwarg_fmt(kw):
        if isinstance(kw, str):
            return kw
        return repr(kw)
    prepr = []
    i = 0
    # TODO: % not format()
    while i < len(path):
        op, arg = path[i], path[i + 1]
        if op == '.':
            prepr.append('.' + arg)
        elif op == '[':
            prepr.append("[{0!r}]".format(arg))
        elif op == '(':
            args, kwargs = arg
            prepr.append("({})".format(
                ", ".join(
                    [repr(a) for a in args] +
                    ["{}={}".format(kwarg_fmt(k), repr(v))
                     for k, v in kwargs.items()])))
        i += 2
    return "".join(prepr)


def _t_eval(_t, target, path, inspector, recurse):
    t_path = _T_PATHS[_t]
    i = 0
    cur = target
    while i < len(t_path):
        op, arg = t_path[i], t_path[i + 1]
        if type(arg) in (Spec, _TType):
            arg = recurse(target, arg, path, inspector)
        if op == '.':
            cur = getattr(cur, arg, _MISSING)
            if cur is _MISSING:
                raise GlomAttributeError(_path_fmt(t_path[:i]))
        elif op == '[':
            try:
                cur = cur[arg]
            except (KeyError, IndexError) as e:
                path = _path_fmt(t_path[:i])
                raise GlomKeyError(_path_fmt(t_path[:i]))
            except IndexError:
                raise GlomIndexError(_path_fmt(t_path[:i]))
        elif op == '(':
            args, kwargs = arg
            cur = recurse(  # TODO: mutate path correctly
                target, Call(cur, args, kwargs), path, inspector)
            # call with target rather than cur,
            # because it is probably more intuitive
            # if args to the call "reset" their path
            # e.g. "T.a" should mean the same thing
            # in both of these specs: T.a and T.b(T.a)
        i += 2
    return cur


T = _TType()
_T_PATHS[T] = ()
UP = make_sentinel('UP')


class _AbstractIterable(_AbstractIterableBase):
    __metaclass__ = ABCMeta
    @classmethod
    def __subclasshook__(cls, C):
        if C in (str, bytes):
            return False
        return callable(getattr(C, "__iter__", None))


def _get_sequence_item(target, index):
    return target[int(index)]


class Glommer(object):
    """All the wholesome goodness that it takes to make glom work. This
    type mostly serves to encapsulate the type registration context so
    that advanced uses of glom don't need to worry about stepping on
    each other's toes.

    Glommer objects are lightweight and, once instantiated, provide
    the :func:`glom()` method we know and love:

    >>> glommer = Glommer()
    >>> glommer.glom({}, 'a.b.c', default='d')
    'd'
    >>> Glommer().glom({'vals': list(range(3))}, ('vals', len))
    3

    Instances also provide :meth:`~Glommer.register()` method for
    localized control over type handling.

    Args:
       register_default_types (bool): Whether or not to enable the
          handling behaviors of the default :func:`glom()`. These
          default actions include dict access, list and iterable
          iteration, and generic object attribute access. Defaults to
          True.

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
        self.register(list, _get_sequence_item)
        self.register(tuple, _get_sequence_item)
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
        """Register *target_type* so :meth:`~Glommer.glom()` will
        know how to handle instances of that type as targets.

        Args:
           target_type (type): A type expected to appear in a glom()
              call target
           get (callable): A function which takes a target object and
              a name, acting as a default accessor. Defaults to
              :func:`getattr`.
           iterate (callable): A function which takes a target object
              and returns an iterator. Defaults to :func:`iter` if
              *target_type* appears to be iterable.
           exact (bool): Whether or not to match instances of subtypes
              of *target_type*.

        .. note::

           The module-level :func:`register()` function affects the
           module-level :func:`glom()` function's behavior. If this
           global effect is undesirable for your application, or
           you're implementing a library, consider instantiating a
           :class:`Glommer` instance, and using the
           :meth:`~Glommer.register()` and :meth:`Glommer.glom()`
           methods instead.

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
                raise PathAccessError(e, parts, i)
            cur = val
        return val

    def glom(self, target, spec, **kwargs):
        """Fetch or construct a new value from a given *target* based on the
        specification declared by *spec*.

        ``glom`` also takes a keyword-argument, *default*. When set, a
        ``glom`` operation fails with a :exc:`GlomError`, the
        *default* will be returned, like :meth:`dict.get()`. The
        *skip_exc* keyword argument controls which errors should be
        ignored.

        Fetch, aka deep-get:

        >>> target = {'a': {'b': 'c'}}
        >>> glom(target, 'a.b')
        'c'

        Construct, aka restructure, aka conglomerate:

        >>> target = {'a': {'b': 'c', 'd': 'e'}, 'f': 'g', 'h': [0, 1, 2]}
        >>> output = glom(target, {'a': 'a.b', 'd': 'a.d', 'h': ('h', [lambda x: x * 2])})
        >>> pprint(output)
        {'a': 'c', 'd': 'e', 'h': [0, 2, 4]}

        Glom's power is only surpassed by its intuitiveness. Give it a whirl!

        Args:
           target (object): the object on which the glom will operate.
           spec (object): Specification of the output object in the form
             of a dict, list, tuple, string, other glom construct, or
             any composition of these.
           default (object): An optional default to return in the case
             an exception, specified by *skip_exc*, is raised.

           skip_exc (Exception): An optional exception or tuple of
             exceptions to ignore and return *default* (None if
             omitted). If *skip_exc* and *default* are both not set,
             glom raises errors through.

        """
        # TODO: check spec up front
        default = kwargs.pop('default', None if 'skip_exc' in kwargs else _MISSING)
        skip_exc = kwargs.pop('skip_exc', () if default is _MISSING else GlomError)
        path = kwargs.pop('path', [])
        inspector = kwargs.pop('inspector', None)
        if kwargs:
            raise TypeError('unexpected keyword args: %r' % sorted(kwargs.keys()))
        try:
            ret = self._glom(target, spec, path=path, inspector=inspector)
        except skip_exc:
            if default is _MISSING:
                raise
            ret = default
        return ret

    def _glom(self, target, spec, path, inspector):
        # TODO: de-recursivize this
        # TODO: rearrange the branching below by frequency of use
        # recursive self._glom() calls should pass path=path to elide the current
        # step, otherwise add the current spec in some fashion
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
                ret = self._glom(target, spec.wrapped, path=path, inspector=spec)
            except Exception:
                if spec.post_mortem:
                    spec.post_mortem()
                raise
        elif isinstance(spec, dict):
            ret = type(spec)() # TODO: works for dict + ordereddict, but sufficient for all?
            for field, sub_spec in spec.items():
                val = self._glom(target, sub_spec, path=path, inspector=next_inspector)
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
                val = self._glom(t, sub_spec, path=path + [i], inspector=inspector)
                if val is OMIT:
                    continue
                ret.append(val)
        elif isinstance(spec, tuple):
            res = target
            for sub_spec in spec:
                res = self._glom(res, sub_spec, path=path, inspector=next_inspector)
                next_inspector = sub_spec if (isinstance(sub_spec, Inspect) and sub_spec.recursive) else next_inspector
                if not isinstance(sub_spec, list):
                    path = path + [getattr(sub_spec, '__name__', sub_spec)]
            ret = res
        elif isinstance(spec, _TType):  # NOTE: must come before callable b/c T is also callable
            ret = _t_eval(spec, target, path, inspector, self._glom)
        elif isinstance(spec, Call):
            ret = spec(target, path, inspector, self._glom)
        elif callable(spec):
            ret = spec(target)
        elif isinstance(spec, (basestring, Path)):
            try:
                ret = self._get_path(target, spec)
            except PathAccessError as pae:
                pae.path = Path(*(path + list(pae.path)))
                pae.path_idx += len(path)
                raise
        elif isinstance(spec, Coalesce):
            skipped = []
            for sub_spec in spec.subspecs:
                try:
                    ret = self._glom(target, sub_spec, path=path, inspector=next_inspector)
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
        elif isinstance(spec, Spec):
            # TODO: this could be switched to a while loop at the top for
            # performance, but don't want to mess around too much yet
            # while(type(target) is Spec): target = target.value
            ret = self._glom(target, spec.value, path=path, inspector=inspector)
        else:
            raise TypeError('expected spec to be dict, list, tuple,'
                            ' callable, string, or other specifier type,'
                            ' not: %r'% spec)
        if inspector and inspector.echo:
            print('output:', ret)
            print()
        return ret


_DEFAULT = Glommer(register_default_types=True)
glom = _DEFAULT.glom
register = _DEFAULT.register


"""TODO:
* "Restructuring Data" / "Restructured Data"

* More subspecs
  * Inspect - mostly done, but performance checking
  * Check() - wraps a subspec, performing checking on its
    return. e.g., Check('a.b.c', type=int, value=1, action='raise') #
    action='omit' maybe also supported, other actions?
  * Specifier types for all the shorthands (e.g., Assign() for {},
    Iterate() for []), allows adding more options in situations that
    need them.
(Call and Target have better aesthetics and repr compared to lambdas, but are otherwise no more capable)
* Call
  * If callable is not intrinsically sufficient for good error
    reporting, make whatever method it has compatible with the _glom()
    signature
  * skip_exc and default arguments to Call, like glom(), for easy try/except
* Target
  * Effectively a path, but with an unambiguous
    getitem/getattr. (should Path and Target merge??)
* Path note: path is ambiguous wrt what access is performed (getitem
  or getattr), should this be rectified, or is it ok to have TARGET be
  a more powerful alternative?
* More supported target types
  * Django and SQLAlchemy Models and QuerySets
  * API for (bypassing) registering known 3rd party integrations like the above
* Top-level option to collect all the errors instead of just the first.
  * This will probably require another context object in addition to
    inspector and path.
* check_spec / audit_spec
  * Forward check all types (remap?)
  * Call(func) <- func must take exactly one argument and have the rest fulfilled by args/kwargs
  * lambdas must also take one argument

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

"""
