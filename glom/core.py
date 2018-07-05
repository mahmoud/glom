"""*glom gets results.*

If there was ever a Python example of "big things come in small
packages", ``glom`` might be it.

The ``glom`` package has one central entrypoint,
:func:`glom.glom`. Everything else in the package revolves around that
one function.

A couple of conventional terms you'll see repeated many times below:

* **target** - glom is built to work on any data, so we simply
  refer to the object being accessed as the *"target"*
* **spec** - *(aka "glomspec", short for specification)* The
  accompanying template used to specify the structure of the return
  value.

Now that you know the terms, let's take a look around glom's powerful
semantics.

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
from boltons.iterutils import is_iterable

PY2 = (sys.version_info[0] == 2)
if PY2:
    _AbstractIterableBase = object
    from .chainmap_backport import ChainMap
else:
    basestring = str
    _AbstractIterableBase = ABCMeta('_AbstractIterableBase', (object,), {})
    from collections import ChainMap

_type_type = type

_MISSING = make_sentinel('_MISSING')
OMIT =  make_sentinel('OMIT')
OMIT.__doc__ = """
The ``OMIT`` singleton can be returned from a function or included
via a :class:`~glom.Literal` to cancel assignment into the output
object.

>>> target = {'a': 'b'}
>>> spec = {'a': lambda t: t['a'] if t['a'] == 'a' else OMIT}
>>> glom(target, spec)
{}
>>> target = {'a': 'a'}
>>> glom(target, spec)
{'a': 'a'}

Mostly used to drop keys from dicts (as above) or filter objects from
lists.

"""


class GlomError(Exception):
    """The base exception for all the errors that might be raised from
    :func:`glom` processing logic.

    By default, exceptions raised from within functions passed to glom
    (e.g., ``len``, ``sum``, any ``lambda``) will not be wrapped in a
    GlomError.
    """
    pass


class PathAccessError(AttributeError, KeyError, IndexError, GlomError):
    """This :exc:`GlomError` subtype represents a failure to access an
    attribute as dictated by the spec. The most commonly-seen error
    when using glom, it maintains a copy of the original exception and
    produces a readable error message for easy debugging.

    If you see this error, you may want to:

       * Check the target data is accurate using :class:`~glom.Inspect`
       * Catch the exception and return a semantically meaningful error message
       * Use :class:`glom.Coalesce` to specify a default
       * Use the top-level ``default`` kwarg on :func:`~glom.glom()`

    In any case, be glad you got this error and not the one it was
    wrapping!

    Args:
       exc (Exception): The error that arose when we tried to access
          *path*. Typically an instance of KeyError, AttributeError,
          IndexError, or TypeError, and sometimes others.
       path (Path): The full Path glom was in the middle of accessing
          when the error occurred.
       part_idx (int): The index of the part of the *path* that caused
          the error.

    >>> target = {'a': {'b': None}}
    >>> glom(target, 'a.b.c')
    Traceback (most recent call last):
    ...
    PathAccessError: could not access 'c', part 2 of Path('a', 'b', 'c'), got error: ...

    """
    def __init__(self, exc, path, part_idx):
        self.exc = exc
        self.path = path
        self.part_idx = part_idx

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.exc, self.path, self.part_idx)

    def __str__(self):
        return ('could not access %r, part %r of %r, got error: %r'
                % (self.path[self.part_idx], self.part_idx, self.path, self.exc))


class CoalesceError(GlomError):
    """This :exc:`GlomError` subtype is raised from within a
    :class:`Coalesce` spec's processing, when none of the subspecs
    match and no default is provided.

    The exception object itself keeps track of several values which
    may be useful for processing:

    Args:
       coal_obj (Coalesce): The original failing spec, see
          :class:`Coalesce`'s docs for details.
       skipped (list): A list of ignored values and exceptions, in the
          order that their respective subspecs appear in the original
          *coal_obj*.
       path: Like many GlomErrors, this exception knows the path at
          which it occurred.

    >>> target = {}
    >>> glom(target, Coalesce('a', 'b'))
    Traceback (most recent call last):
    ...
    CoalesceError: no valid values found. Tried ('a', 'b') and got (PathAccessError, PathAccessError) ...
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
        msg = ('no valid values found. Tried %r and got (%s)'
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
    production glom usage. See the :ref:`setup-and-registration`
    section for details on how to avoid this error.

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
        # <type %r> is because Python 3 inexplicably changed the type
        # repr from <type *> to <class *>
        return ('%s(%r, <type %r>, %r, %r)'
                % (cn, self.op, self.target_type.__name__, self.type_map, self.path))

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

    def __repr__(self):
        return ('<%s object type=%s get=%s iterate=%s>'
                % (self.__class__.__name__,
                   self.type.__name__,
                   self.get and self.get.__name__,
                   self.iterate and self.iterate.__name__))


class Path(object):
    """Path objects specify explicit paths when the default ``'a.b.c'``-style
    general access syntax won't work or isn't desirable.
    Use this to wrap ints, datetimes, and other valid keys, as well as
    strings with dots that shouldn't be expanded.

    >>> target = {'a': {'b': 'c', 'd.e': 'f', 2: 3}}
    >>> glom(target, Path('a', 2))
    3
    >>> glom(target, Path('a', 'd.e'))
    'f'

    Paths can also be used to join together :data:`~glom.T` objects:

    >>> Path(T['a'], T['b'])
    T['a']['b']

    """
    def __init__(self, *path_parts):
        path_t = T
        for part in path_parts:
            if isinstance(part, Path):
                part = part.path_t
            if isinstance(part, _TType):
                sub_parts = _T_PATHS[part]
                if sub_parts[0] is not T:
                    raise ValueError('path segment must be path from T, not %r'
                                     % sub_parts[0])
                i = 1
                while i < len(sub_parts):
                    path_t = _t_child(path_t, sub_parts[i], sub_parts[i + 1])
                    i += 2
            else:
                path_t = _t_child(path_t, 'P', part)
        self.path_t = path_t

    def append(self, part):
        assert not isinstance(part, _TType), "call extend or +?"
        assert not isinstance(part, Path), "call extend or +?"
        self.path_t = _t_child(self.path_t, 'P', part)

    def _handler(self, target, scope):
        return _t_eval(self.path_t, target, scope)

    def __getitem__(self, idx):
        # used by PathAccessError
        # 1 + skips the first T/S and operator
        return _T_PATHS[self.path_t][(1 + idx) * 2]

    def __repr__(self):
        return _format_path(_T_PATHS[self.path_t][1:])


def _format_path(t_path):
    path_parts, cur_t_path = [], []
    i = 0
    while i < len(t_path):
        op, arg = t_path[i], t_path[i + 1]
        i += 2
        if op == 'P':
            if cur_t_path:
                path_parts.append(cur_t_path)
                cur_t_path = []
            path_parts.append(arg)
        else:
            cur_t_path.append(op)
            cur_t_path.append(arg)
    if path_parts and cur_t_path:
        path_parts.append(cur_t_path)

    if path_parts or not cur_t_path:
        return 'Path(%s)' % ', '.join([_format_t(part)
                                       if type(part) is list else repr(part)
                                       for part in path_parts])
    return _format_t(cur_t_path)


class Literal(object):
    """Literal objects specify literal values in rare cases when part of
    the spec should not be interpreted as a glommable
    subspec. Wherever a Literal object is encountered in a spec, it is
    replaced with its wrapped *value* in the output.

    >>> target = {'a': {'b': 'c'}}
    >>> spec = {'a': 'a.b', 'readability': Literal('counts')}
    >>> pprint(glom(target, spec))
    {'a': 'c', 'readability': 'counts'}

    Instead of accessing ``'counts'`` as a key like it did with
    ``'a.b'``, :func:`~glom.glom` just unwrapped the literal and
    included the value.

    :class:`~glom.Literal` takes one argument, the literal value that should appear
    in the glom output.

    This could also be achieved with a callable, e.g., ``lambda x:
    'literal_string'`` in the spec, but using a :class:`~glom.Literal`
    object adds explicitness, code clarity, and a clean :func:`repr`.

    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r)' % (cn, self.value)


class Spec(object):
    """Spec objects serve three purposes, here they are, roughly ordered
    by utility:

      1. As a form of compiled or "curried" glom call, similar to
         Python's built-in :func:`re.compile`.
      2. A marker as an object as representing a spec rather than a
         literal value in certain cases where that might be ambiguous.
      3. A way to update the scope within another Spec.

    In the second usage, Spec objects are the complement to
    :class:`~glom.Literal`, wrapping a value and marking that it
    should be interpreted as a glom spec, rather than a literal value.
    This is useful in places where it would be interpreted as a value
    by default. (Such as T[key], Call(func) where key and func are
    assumed to be literal values and not specs.)

    Args:
        spec: The glom spec.
        scope (dict): additional values to add to the scope when
          evaluating this Spec

    """
    def __init__(self, spec, scope=None):
        self.spec = spec
        self.scope = scope or {}

    def glom(self, target, **kw):
        scope = dict(self.scope)
        scope.update(kw.get('scope', {}))
        kw['scope'] = scope
        return glom(target, self.spec, **kw)

    def _handler(self, target, scope):
        scope.update(self.scope)
        return scope[glom](target, self.spec, scope)

    def __repr__(self):
        cn = self.__class__.__name__
        if self.scope:
            return '%s(%r, scope=%r)' % (cn, self.spec, self.scope)
        return '%s(%r)' % (cn, self.spec)


class Coalesce(object):
    """Coalesce objects specify fallback behavior for a list of
    subspecs.

    Subspecs are passed as positional arguments, and keyword arguments
    control defaults. Each subspec is evaluated in turn, and if none
    match, a :exc:`CoalesceError` is raised, or a default is returned,
    depending on the options used.

    .. note::

      This operation may seem very familar if you have experience with
      `SQL`_ or even `C# and others`_.


    In practice, this fallback behavior's simplicity is only surpassed
    by its utility:

    >>> target = {'c': 'd'}
    >>> glom(target, Coalesce('a', 'b', 'c'))
    'd'

    glom tries to get ``'a'`` from ``target``, but gets a
    KeyError. Rather than raise a :exc:`~glom.PathAccessError` as usual,
    glom *coalesces* into the next subspec, ``'b'``. The process
    repeats until it gets to ``'c'``, which returns our value,
    ``'d'``. If our value weren't present, we'd see:

    >>> target = {}
    >>> glom(target, Coalesce('a', 'b'))
    Traceback (most recent call last):
    ...
    CoalesceError: no valid values found. Tried ('a', 'b') and got (PathAccessError, PathAccessError) ...

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
       default_factory: A callable whose result will be returned as a default
       skip: A value, tuple of values, or predicate function
         representing values to ignore
       skip_exc: An exception or tuple of exception types to catch and
         move on to the next subspec. Defaults to :exc:`GlomError`, the
         parent type of all glom runtime exceptions.

    If all subspecs produce skipped values or exceptions, a
    :exc:`CoalesceError` will be raised. For more examples, check out
    the :doc:`tutorial`, which makes extensive use of Coalesce.

    .. _SQL: https://en.wikipedia.org/w/index.php?title=Null_(SQL)&oldid=833093792#COALESCE
    .. _C# and others: https://en.wikipedia.org/w/index.php?title=Null_coalescing_operator&oldid=839493322#C#

    """
    def __init__(self, *subspecs, **kwargs):
        self.subspecs = subspecs
        self.default = kwargs.pop('default', _MISSING)
        self.default_factory = kwargs.pop('default_factory', _MISSING)
        if self.default and self.default_factory:
            raise ValueError('expected one of "default" or "default_factory", not both')
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

    def _handler(self, target, scope):
        skipped = []
        for subspec in self.subspecs:
            try:
                ret = scope[glom](target, subspec, scope)
                if not self.skip_func(ret):
                    break
                skipped.append(ret)
            except self.skip_exc as e:
                skipped.append(e)
                continue
        else:
            if self.default is not _MISSING:
                ret = self.default
            elif self.default_factory is not _MISSING:
                ret = self.default_factory()
            else:
                raise CoalesceError(self, skipped, scope[Path])
        return ret


class Inspect(object):
    """The :class:`~glom.Inspect` specifier type provides a way to get
    visibility into glom's evaluation of a specification, enabling
    debugging of those tricky problems that may arise with unexpected
    data.

    :class:`~glom.Inspect` can be inserted into an existing spec in one of two
    ways. First, as a wrapper around the spec in question, or second,
    as an argument-less placeholder wherever a spec could be.

    :class:`~glom.Inspect` supports several modes, controlled by
    keyword arguments. Its default, no-argument mode, simply echos the
    state of the glom at the point where it appears:

      >>> target = {'a': {'b': {}}}
      >>> val = glom(target, Inspect('a.b'))  # wrapping a spec
      ---
      path:   ['a.b']
      target: {'a': {'b': {}}}
      output: {}
      ---

    Debugging behavior aside, :class:`~glom.Inspect` has no effect on
    values in the target, spec, or result.

    Args:
       echo (bool): Whether to print the path, target, and output of
         each inspected glom. Defaults to True.
       recursive (bool): Whether or not the Inspect should be applied
         at every level, at or below the spec that it wraps. Defaults
         to False.
       breakpoint (bool): This flag controls whether a debugging prompt
         should appear before evaluating each inspected spec. Can also
         take a callable. Defaults to False.
       post_mortem (bool): This flag controls whether exceptions
         should be caught and interactively debugged with :mod:`pdb` on
         inspected specs.

    All arguments above are keyword-only to avoid overlap with a
    wrapped spec.

    .. note::

       Just like ``pdb.set_trace()``, be careful about leaving stray
       ``Inspect()`` instances in production glom specs.

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

    def _handler(self, target, scope):
        # stash the real handler under Inspect,
        # and replace the child handler with a trace callback
        scope[Inspect] = scope[glom]
        scope[glom] = self._trace
        return scope[glom](target, self.wrapped, scope)

    def _trace(self, target, spec, scope):
        if not self.recursive:
            scope[glom] = scope[Inspect]
        if self.echo:
            print('---')
            print('path:  ', scope[Path] + [spec])
            print('target:', target)
        if self.breakpoint:
            self.breakpoint()
        try:
            ret = scope[Inspect](target, self.wrapped, scope)
        except Exception:
            if self.post_mortem:
                self.post_mortem()
            raise
        if self.echo:
            print('output:', ret)
            print('---')
        return ret


class Call(object):
    """:class:`Call` specifies when a target should be passed to a function,
    *func*.

    :class:`Call` is similar to :func:`~functools.partial` in that
    it is no more powerful than ``lambda`` or other functions, but
    it is designed to be more readable, with a better ``repr``.

    Args:
       func (callable): a function or other callable to be called with
          the target

    :class:`Call` combines well with :attr:`~glom.T` to construct objects. For
    instance, to generate a dict and then pass it to a constructor:

    >>> class ExampleClass(object):
    ...    def __init__(self, attr):
    ...        self.attr = attr
    ...
    >>> target = {'attr': 3.14}
    >>> glom(target, Call(ExampleClass, kwargs=T)).attr
    3.14

    This does the same as ``glom(target, lambda target:
    ExampleClass(**target))``, but it's easy to see which one reads
    better.

    .. note::

       ``Call`` is mostly for functions. Use a :attr:`~glom.T` object
       if you need to call a method.

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

    def _handler(self, target, scope):
        'run against the current target'
        def eval(t):
            if type(t) in (Spec, _TType):
                return scope[glom](target, t, scope)
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
        cn = self.__class__.__name__
        return '%s(%r, args=%r, kwargs=%r)' % (cn, self.func, self.args, self.kwargs)


class _TType(object):
    """``T``, short for "target". A singleton object that enables
    object-oriented expression of a glom specification.

    .. note::

       ``T`` is a singleton, and does not need to be constructed.

    Basically, think of ``T`` as your data's stunt double. Everything
    that you do to ``T`` will be recorded and executed during the
    :func:`glom` call. Take this example:

    >>> spec = T['a']['b']['c']
    >>> target = {'a': {'b': {'c': 'd'}}}
    >>> glom(target, spec)
    'd'

    So far, we've relied on the ``'a.b.c'``-style shorthand for
    access, or used the :class:`~glom.Path` objects, but if you want
    to explicitly do attribute and key lookups, look no further than
    ``T``.

    But T doesn't stop with unambiguous access. You can also call
    methods and perform almost any action you would with a normal
    object:

    >>> spec = ('a', (T['b'].items(), list))  # reviewed below
    >>> glom(target, spec)
    [('c', 'd')]

    A ``T`` object can go anywhere in the spec. As seen in the example
    above, we access ``'a'``, use a ``T`` to get ``'b'`` and iterate
    over its ``items``, turning them into a ``list``.

    You can even use ``T`` with :class:`~glom.Call` to construct objects:

    >>> class ExampleClass(object):
    ...    def __init__(self, attr):
    ...        self.attr = attr
    ...
    >>> target = {'attr': 3.14}
    >>> glom(target, Call(ExampleClass, kwargs=T)).attr
    3.14

    On a further note, while ``lambda`` works great in glom specs, and
    can be very handy at times, ``T`` and :class:`~glom.Call`
    eliminate the need for the vast majority of ``lambda`` usage with
    glom.

    Unlike ``lambda`` and other functions, ``T`` roundtrips
    beautifully and transparently:

    >>> T['a'].b['c']('success')
    T['a'].b['c']('success')

    ``T``-related access errors raise a :exc:`~glom.PathAccessError`
    during the :func:`~glom.glom` call.

    .. note::

       While ``T`` is clearly useful, powerful, and here to stay, its
       semantics are still being refined. Currently, operations beyond
       method calls and attribute/item access are considered
       experimental and should not be relied upon.

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
        return _format_t(_T_PATHS[self][1:])


def _format_t(path):
    def kwarg_fmt(kw):
        if isinstance(kw, str):
            return kw
        return repr(kw)
    prepr = ['T']
    i = 0
    while i < len(path):
        op, arg = path[i], path[i + 1]
        if op == '.':
            prepr.append('.' + arg)
        elif op == '[':
            prepr.append("[%r]" % (arg,))
        elif op == '(':
            args, kwargs = arg
            prepr.append("(%s)" % ", ".join([repr(a) for a in args] +
                                            ["%s=%r" % (kwarg_fmt(k), v)
                                             for k, v in kwargs.items()]))
        elif op == 'P':
            return _format_path(path)
        i += 2
    return "".join(prepr)


_T_PATHS = weakref.WeakKeyDictionary()


def _t_child(parent, operation, arg):
    t = _TType()
    _T_PATHS[t] = _T_PATHS[parent] + (operation, arg)
    return t


def _t_eval(_t, target, scope):
    t_path = _T_PATHS[_t]
    i = 1
    if t_path[0] is T:
        cur = target
    elif t_path[0] is S:
        cur = scope
    else:
        raise ValueError('_TType instance with invalid root object')
    while i < len(t_path):
        op, arg = t_path[i], t_path[i + 1]
        if type(arg) in (Spec, _TType):
            arg = scope[glom](target, arg, scope)
        if op == '.':
            try:
                cur = getattr(cur, arg)
            except AttributeError as e:
                raise PathAccessError(e, Path(_t), i // 2)
        elif op == '[':
            try:
                cur = cur[arg]
            except (KeyError, IndexError, TypeError) as e:
                raise PathAccessError(e, Path(_t), i // 2)
        elif op == 'P':
            # Path type stuff (fuzzy match)
            handler = scope[_TargetRegistry].get_handler(cur)
            if not handler.get:
                raise UnregisteredTarget(
                    'get', type(target), scope[_TargetRegistry]._type_map, path=t_path[2:i+2:2])
            try:
                cur = handler.get(cur, arg)
            except Exception as e:
                raise PathAccessError(e, Path(_t), i // 2)
        elif op == '(':
            args, kwargs = arg
            scope[Path] += t_path[2:i+2:2]
            cur = scope[glom](
                target, Call(cur, args, kwargs), scope)
            # call with target rather than cur,
            # because it is probably more intuitive
            # if args to the call "reset" their path
            # e.g. "T.a" should mean the same thing
            # in both of these specs: T.a and T.b(T.a)
        i += 2
    return cur


T = _TType()  # target aka Mr. T aka "this"
S = _TType()  # like T, but means grab stuff from Scope, not Target

_T_PATHS[T] = (T,)
_T_PATHS[S] = (S,)
UP = make_sentinel('UP')


class CheckError(GlomError):
    def __init__(self, msgs, check, path):
        self.msgs = msgs
        self.check_obj = check
        self.path = path

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.msgs, self.check_obj, self.path)

    def __str__(self):
        msg = 'target at path %s failed check,' % self.path
        if self.check_obj.spec is not T:
            msg += ' subtarget at %r' % (self.check_obj.spec,)
        if len(self.msgs) == 1:
            msg += ' got error: %r' % (self.msgs[0],)
        else:
            msg += ' got %s errors: %r' % (len(self.msgs), self.msgs)
        return msg


RAISE = make_sentinel('RAISE')  # flag object for "raise on check failure"


class Check(object):
    """Check objects are used to make assertions about the target data,
    and either pass through the data or raise exceptions if there is a
    problem.

    Aside from *spec*, all arguments are keyword arguments. Each
    argument, except for *default*, represent a check
    condition. Multiple checks can be passed, and if all check
    conditions are left unset, Check defaults to performing a basic
    truthy check on the value.

    If any check condition fails, a :class:`~glom.GlomCheckError` is raised.

    Args:

       spec: a sub-spec to extract the data to which other assertions will
          be checked (defaults to applying checks to the target itself)
       type: a type or sequence of types to be checked for exact match
       equal_to: a value to be checked for equality match ("==")
       validate: a callable or list of callables, each representing a
          check condition. If one or more return False or raise an
          exception, the Check will fail.
       instance_of: a type or sequence of types to be checked with isinstance()
       one_of: an iterable of values, any of which can match the target ("in")
       default: an optional default value to replace the value when the check fails
                (if default is not specified, GlomCheckError will be raised)

    """
    # TODO: the next level of Check would be to play with the Scope to
    # allow checking to continue across the same level of
    # dictionary. Basically, collect as many errors as possible before
    # raising the unified CheckError.
    def __init__(self, spec=T, **kwargs):
        self.spec = spec
        self.default = kwargs.pop('default', RAISE)

        def _get_arg_val(name, cond, func, val, can_be_empty=True):
            if val is _MISSING:
                return ()
            if not is_iterable(val):
                val = (val,)
            elif not val and not can_be_empty:
                raise ValueError('expected %r argument to contain at least one value,'
                                 ' not: %r' % (name, val))
            for v in val:
                if not func(v):
                    raise ValueError('expected %r argument to be %s, not: %r'
                                     % (name, cond, v))
            return val

        # if there are other common validation functions, maybe a
        # small set of special strings would work as valid arguments
        # to validate, too.
        def truthy(val):
            return bool(val)

        validate = kwargs.pop('validate', _MISSING if kwargs else truthy)
        type_arg = kwargs.pop('type', _MISSING)
        instance_of = kwargs.pop('instance_of', _MISSING)
        equal_to = kwargs.pop('equal_to', _MISSING)
        one_of = kwargs.pop('one_of', _MISSING)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % kwargs.keys())

        self.validators = _get_arg_val('validate', 'callable', callable, validate)
        self.instance_of = _get_arg_val('instance_of', 'a type',
                                        lambda x: isinstance(x, type), instance_of, False)
        self.types = _get_arg_val('type', 'a type',
                                  lambda x: isinstance(x, type), type_arg, False)

        if equal_to is not _MISSING:
            self.vals = (equal_to,)
            if one_of is not _MISSING:
                raise TypeError('expected "one_of" argument to be unset when'
                                ' "equal_to" argument is passed')
        elif one_of is not _MISSING:
            if not is_iterable(one_of):
                raise ValueError('expected "one_of" argument to be iterable'
                                 ' , not: %r' % one_of)
            if not one_of:
                raise ValueError('expected "one_of" to contain at least'
                                 ' one value, not: %r' % (one_of,))
            self.vals = one_of
        else:
            self.vals = ()
        return

    class _ValidationError(Exception):
        "for internal use inside of Check only"
        pass

    def _handler(self, target, scope):
        ret = target
        errs = []
        if self.spec is not T:
            target = scope[glom](target, self.spec, scope)
        if self.types and type(target) not in self.types:
            if self.default is not RAISE:
                return self.default
            errs.append('expected type to be %r, found type %r' %
                        (self.types[0].__name__ if len(self.types) == 1
                         else tuple([t.__name__ for t in self.types]),
                         type(target).__name__))

        if self.vals and target not in self.vals:
            if self.default is not RAISE:
                return self.default
            if len(self.vals) == 1:
                errs.append("expected {}, found {}".format(self.vals[0], target))
            else:
                errs.append('expected one of {}, found {}'.format(self.vals, target))

        if self.validators:
            for i, validator in enumerate(self.validators):
                try:
                    res = validator(target)
                    if res is False:
                        raise self._ValidationError
                except Exception as e:
                    msg = ('expected %r check to validate target'
                           % getattr(validator, '__name__', None) or ('#%s' % i))
                    if type(e) is not self._ValidationError:
                        msg += ' (got exception: %r)' % e
                    errs.append(msg)

        if self.instance_of and not isinstance(target, self.instance_of):
            # TODO: can these early returns be done without so much copy-paste?
            # (early return to avoid potentially expensive or even error-causeing
            # string formats)
            if self.default is not RAISE:
                return self.default
            errs.append('expected instance of %r, found instance of %r' %
                        (self.instance_of[0].__name__ if len(self.instance_of) == 1
                         else tuple([t.__name__ for t in self.instance_of]),
                         type(target).__name__))


        if errs:
            # TODO: due to the usage of basic path (not a Path
            # object), the format can be a bit inconsistent here
            # (e.g., 'a.b' and ['a', 'b'])
            raise CheckError(errs, self, scope[Path])
        return ret


class _AbstractIterable(_AbstractIterableBase):
    __metaclass__ = ABCMeta
    @classmethod
    def __subclasshook__(cls, C):
        if C in (str, bytes):
            return False
        return callable(getattr(C, "__iter__", None))


def _get_sequence_item(target, index):
    return target[int(index)]


# handlers are 3-arg callables, with args (spec, target, scope)
# spec is the first argument for convenience in the case
# that the handler is a method of the spec type
def _handle_dict(spec, target, scope):
    ret = type(spec)() # TODO: works for dict + ordereddict, but sufficient for all?
    for field, subspec in spec.items():
        val = scope[glom](target, subspec, scope)
        if val is OMIT:
            continue
        ret[field] = val
    return ret


def _handle_list(spec, target, scope):
    subspec = spec[0]
    handler = scope[_TargetRegistry].get_handler(target)
    if not handler.iterate:
        raise UnregisteredTarget('iterate', type(target), scope[_TargetRegistry]._type_map, path=scope[Path])
    try:
        iterator = handler.iterate(target)
    except Exception as e:
        te = TypeError('failed to iterate on instance of type %r at %r (got %r)'
                        % (target.__class__.__name__, Path(*scope[Path]), e))
        print(te)
        raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                        % (target.__class__.__name__, Path(*scope[Path]), e))
    ret = []
    for i, t in enumerate(iterator):
        val = scope[glom](t, subspec, scope.new_child({Path: scope[Path] + [i]}))
        if val is OMIT:
            continue
        ret.append(val)
    return ret


def _handle_tuple(spec, target, scope):
    res = target
    for subspec in spec:
        res = scope[glom](res, subspec, scope)
        if not isinstance(subspec, list):
            scope[Path] += [getattr(subspec, '__name__', subspec)]
    return res


class _SpecRegistry(object):
    '''
    responsible for registration of spec types
    '''
    def __init__(self, specs):
        '''
        specs should be ((type, handler), (type, handler), ...)
        '''
        self.specs = specs

    def get_handler(self, spec):
        'return handler callable that was registered or None'
        for type_, handler in self.specs:
            if type_ is callable and callable(spec):
                return handler
            if type_ is not callable and isinstance(spec, type_):
                return handler
        raise TypeError(
            'no handler for specs of type %s; expected one of %s'
                % (type(spec), ', '.join([e[0].__name__ for e in self.specs])))
        # TODO: don't lose anything from older error message
        # raise TypeError('expected spec to be dict, list, tuple,'
        #                 ' callable, string, or other specifier type,'
        #                 ' not: %r'% spec)


    def register(self, spec_type, spec_handler):
        '''
        given a spec_type and a handler callback
        that accepts (spec, target, scope),
        add the callback to this registry with
        highest precedence
        '''
        self.specs = ((spec_type, spec_handler),) + self.specs


_DEFAULT_SPEC_REGISTRY = _SpecRegistry((
    (Inspect, Inspect._handler),
    (dict, _handle_dict),
    (list, _handle_list),
    (tuple, _handle_tuple),
    (basestring, lambda spec, target, scope: Path(*spec.split('.'))._handler(target, scope)),
    (Path, Path._handler),
    (Coalesce, Coalesce._handler),
    (Check, Check._handler),
    (_TType, _t_eval),  # NOTE: must come before callable b/c T is also callable
    (Call, Call._handler),
    (Spec, Spec._handler),
    (callable, lambda spec, target, scope: spec(target)),
    (Literal, lambda spec, target, scope: spec.value),
    (Spec, lambda spec, target, scope: scope[glom](target, spec.value, scope)),
))


class _TargetRegistry(object):
    '''
    responsible for registration of target types for iteration
    and attribute walking
    '''
    def __init__(self, register_default_types=True):
        self._type_map = OrderedDict()
        self._type_tree = OrderedDict()  # see _register_fuzzy_type for details
        if register_default_types:
            self._register_default_types()
        self._unreg_handler = TargetHandler(None, get=False, iterate=False)

    def get_handler(self, obj):
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
        if not isinstance(target_type, type):
            raise TypeError('register expected a type, not an instance: %r' % (target_type,))
        self._type_map[target_type] = TargetHandler(target_type, get=get, iterate=iterate)
        if not exact:
            self._register_fuzzy_type(target_type)
        return


_DEFAULT_SCOPE = ChainMap({})


def glom(target, spec, **kwargs):
    """Access or construct a value from a given *target* based on the
    specification declared by *spec*.

    Accessing nested data, aka deep-get:

    >>> target = {'a': {'b': 'c'}}
    >>> glom(target, 'a.b')
    'c'

    Here the *spec* was just a string denoting a path,
    ``'a.b.``. As simple as it should be. The next example shows
    how to use nested data to access many fields at once, and make
    a new nested structure.

    Constructing, or restructuring more-complicated nested data:

    >>> target = {'a': {'b': 'c', 'd': 'e'}, 'f': 'g', 'h': [0, 1, 2]}
    >>> spec = {'a': 'a.b', 'd': 'a.d', 'h': ('h', [lambda x: x * 2])}
    >>> output = glom(target, spec)
    >>> pprint(output)
    {'a': 'c', 'd': 'e', 'h': [0, 2, 4]}

    ``glom`` also takes a keyword-argument, *default*. When set,
    if a ``glom`` operation fails with a :exc:`GlomError`, the
    *default* will be returned, very much like
    :meth:`dict.get()`:

    >>> glom(target, 'a.xx', default='nada')
    'nada'

    The *skip_exc* keyword argument controls which errors should
    be ignored.

    >>> glom({}, lambda x: 100.0 / len(x), default=0.0, skip_exc=ZeroDivisionError)
    0.0

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
       scope (dict): Additional data that can be accessed
         via S inside the glom-spec.

    It's a small API with big functionality, and glom's power is
    only surpassed by its intuitiveness. Give it a whirl!

    """
    # TODO: check spec up front
    default = kwargs.pop('default', None if 'skip_exc' in kwargs else _MISSING)
    skip_exc = kwargs.pop('skip_exc', () if default is _MISSING else GlomError)
    scope = _DEFAULT_SCOPE.new_child({
        Path: kwargs.pop('path', []),
        Inspect: kwargs.pop('inspector', None)
    })
    scope.update(kwargs.pop('scope', {}))
    if kwargs:
        raise TypeError('unexpected keyword args: %r' % sorted(kwargs.keys()))
    try:
        ret = _glom(target, spec, scope)
    except skip_exc:
        if default is _MISSING:
            raise
        ret = default
    return ret


def _glom(target, spec, scope):
    scope = scope.new_child()
    scope[T] = target
    return scope[_SpecRegistry].get_handler(spec)(spec, target, scope)


_DEFAULT_SCOPE.update({
    glom: _glom,
    _TargetRegistry: _TargetRegistry(register_default_types=True),
    _SpecRegistry: _DEFAULT_SPEC_REGISTRY
})


def register(target_type, get=None, iterate=None, exact=False):
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
    _DEFAULT_SCOPE[_TargetRegistry].register(target_type, get, iterate, exact)
    return


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
    def __init__(self, register_default_types=True, scope=_DEFAULT_SCOPE):
        # this "freezes" the scope in at the time of construction
        self.scope = ChainMap(dict(scope))
        self.scope[_TargetRegistry] = _TargetRegistry(register_default_types)
        self.scope[_SpecRegistry] = _DEFAULT_SPEC_REGISTRY
        return

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
        self.scope[_TargetRegistry].register(target_type, get, iterate, exact)
        return

    def glom(self, target, spec, **kwargs):
        return glom(target, spec, scope=self.scope, **kwargs)


pass # this line prevents the docstring below from attaching to register


"""TODO:
* "Restructuring Data" / "Restructured Data"

* More subspecs
  * Inspect - mostly done, but performance checking
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
  * empty coalesces?
  * stray Inspect objects
* testing todo: properties that raise exception, other operators that
  raise exceptions.
* Inspect stuff should come out on stderr

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
