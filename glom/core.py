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
from boltons.funcutils import format_invocation

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
SKIP =  make_sentinel('SKIP')
SKIP.__doc__ = """
The ``SKIP`` singleton can be returned from a function or included
via a :class:`~glom.Literal` to cancel assignment into the output
object.

>>> target = {'a': 'b'}
>>> spec = {'a': lambda t: t['a'] if t['a'] == 'a' else SKIP}
>>> glom(target, spec)
{}
>>> target = {'a': 'a'}
>>> glom(target, spec)
{'a': 'a'}

Mostly used to drop keys from dicts (as above) or filter objects from
lists.

.. note::

   SKIP was known as OMIT in versions 18.3.1 and prior. Versions 19+
   will remove the OMIT alias entirely.
"""
OMIT = SKIP  # backwards compat, remove in 19+

STOP = make_sentinel('STOP')
STOP.__doc__ = """
The ``STOP`` singleton can be used to halt iteration of a list or
execution of a tuple of subspecs.

>>> target = range(10)
>>> spec = [lambda x: x if x < 5 else STOP]
>>> glom(target, spec)
[0, 1, 2, 3, 4]
"""

LAST_CHILD_SCOPE = make_sentinel('LAST_CHILD_SCOPE')
LAST_CHILD_SCOPE.__doc__ = """
Marker that can be used by parents to keep track of the last child
scope executed.  Useful for "lifting" results out of child scopes
for scopes that want to chain the scopes of their children together
similar to tuple.
"""
MODE =  make_sentinel('MODE')



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
                % (self.path.values()[self.part_idx], self.part_idx, self.path, self.exc))


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
            return ("glom() called without registering any types for operation '%s'. see"
                    " glom.register() or Glommer's constructor for details." % (self.op,))
        reg_types = sorted([t.__name__ for t, h in self.type_map.items() if h])
        reg_types_str = '()' if not reg_types else ('(%s)' % ', '.join(reg_types))
        msg = ("target type %r not registered for '%s', expected one of"
               " registered types: %s" % (self.target_type.__name__, self.op, reg_types_str))
        if self.path:
            msg += ' (at %r)' % (self.path,)
        return msg


class Path(object):
    """Path objects specify explicit paths when the default
    ``'a.b.c'``-style general access syntax won't work or isn't
    desirable. Use this to wrap ints, datetimes, and other valid
    keys, as well as strings with dots that shouldn't be expanded.

    >>> target = {'a': {'b': 'c', 'd.e': 'f', 2: 3}}
    >>> glom(target, Path('a', 2))
    3
    >>> glom(target, Path('a', 'd.e'))
    'f'

    Paths can be used to join together other Path objects, as
    well as :data:`~glom.T` objects:

    >>> Path(T['a'], T['b'])
    T['a']['b']
    >>> Path(Path('a', 'b'), Path('c', 'd'))
    Path('a', 'b', 'c', 'd')

    Paths also support indexing and slicing, with each access
    returning a new Path object:

    >>> path = Path('a', 'b', 1, 2)
    >>> path[0]
    Path('a')
    >>> path[-2:]
    Path(1, 2)
    """
    def __init__(self, *path_parts):
        if not path_parts:
            self.path_t = T
            return
        if isinstance(path_parts[0], TType):
            path_t = path_parts[0]
            offset = 1
        else:
            path_t = T
            offset = 0
        for part in path_parts[offset:]:
            if isinstance(part, Path):
                part = part.path_t
            if isinstance(part, TType):
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

    @classmethod
    def from_text(cls, text):
        """Make a Path from .-delimited text:

        >>> Path.from_text('a.b.c')
        Path('a', 'b', 'c')

        """
        return cls(*text.split('.'))

    def glomit(self, target, scope):
        # The entrypoint for the Path extension
        return _t_eval(target, self.path_t, scope)

    def __len__(self):
        return (len(_T_PATHS[self.path_t]) - 1) // 2

    def __eq__(self, other):
        if type(other) is Path:
            return _T_PATHS[self.path_t] == _T_PATHS[other.path_t]
        elif type(other) is TType:
            return _T_PATHS[self.path_t] == _T_PATHS[other]
        return False

    def __ne__(self, other):
        return not self == other

    def values(self):
        """
        Returns a tuple of values referenced in this path.

        >>> Path(T.a.b, 'c', T['d']).values()
        ('a', 'b', 'c', 'd')
        """
        cur_t_path = _T_PATHS[self.path_t]
        return cur_t_path[2::2]

    def items(self):
        """
        Returns a tuple of (operation, value) pairs.

        >>> Path(T.a.b, 'c', T['d']).items()
        (('.', 'a'), ('.', 'b'), ('P', 'c'), ('[', 'd'))

        """
        cur_t_path = _T_PATHS[self.path_t]
        return tuple(zip(cur_t_path[1::2], cur_t_path[2::2]))

    def startswith(self, other):
        if isinstance(other, basestring):
            other = Path(other)
        if isinstance(other, Path):
            other = other.path_t
        if not isinstance(other, TType):
            raise TypeError('can only check if Path starts with string, Path or T')
        o_path = _T_PATHS[other]
        return _T_PATHS[self.path_t][:len(o_path)] == o_path

    def from_t(self):
        '''return the same path but starting from T'''
        t_path = _T_PATHS[self.path_t]
        if t_path[0] is S:
            new_t = TType()
            _T_PATHS[new_t] = (T,) + t_path[1:]
            return Path(new_t)
        return self

    def __getitem__(self, i):
        cur_t_path = _T_PATHS[self.path_t]
        try:
            step = i.step
            start = i.start if i.start is not None else 0
            stop = i.stop

            start = (start * 2) + 1 if start >= 0 else (start * 2) + len(cur_t_path)
            if stop is not None:
                stop = (stop * 2) + 1 if stop >= 0 else (stop * 2) + len(cur_t_path)
        except AttributeError:
            step = 1
            start = (i * 2) + 1 if i >= 0 else (i * 2) + len(cur_t_path)
            if start < 0 or start > len(cur_t_path):
                raise IndexError('Path index out of range')
            stop = ((i + 1) * 2) + 1 if i >= 0 else ((i + 1) * 2) + len(cur_t_path)

        new_t = TType()
        new_path = cur_t_path[start:stop]
        if step is not None and step != 1:
            new_path = tuple(zip(new_path[::2], new_path[1::2]))[::step]
            new_path = sum(new_path, ())
        _T_PATHS[new_t] = (cur_t_path[0],) + new_path
        return Path(new_t)

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

    def glomit(self, target, scope):
        return self.value

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
        kw['scope'] = ChainMap(scope)
        glom_ = scope.get(glom, glom)
        return glom_(target, self.spec, **kw)

    def glomit(self, target, scope):
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
        self._orig_kwargs = dict(kwargs)
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

    def glomit(self, target, scope):
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

    def __repr__(self):
        cn = self.__class__.__name__
        return format_invocation(cn, self.subspecs, self._orig_kwargs)


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

    def glomit(self, target, scope):
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
            ret = scope[Inspect](target, spec, scope)
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

    .. warning::

       :class:`Call` has a successor with a fuller-featured API, new
       in 19.3.0: the :class:`Invoke` specifier type.
    """
    def __init__(self, func=None, args=None, kwargs=None):
        if func is None:
            func = T
        if not (callable(func) or isinstance(func, (Spec, TType))):
            raise TypeError('expected func to be a callable or T'
                            ' expression, not: %r' % (func,))
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        self.func, self.args, self.kwargs = func, args, kwargs

    def glomit(self, target, scope):
        'run against the current target'
        def _eval(t):
            if type(t) in (Spec, TType):
                return scope[glom](target, t, scope)
            return t
        if type(self.args) is TType:
            args = _eval(self.args)
        else:
            args = [_eval(a) for a in self.args]
        if type(self.kwargs) is TType:
            kwargs = _eval(self.kwargs)
        else:
            kwargs = {name: _eval(val) for name, val in self.kwargs.items()}
        return _eval(self.func)(*args, **kwargs)

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, args=%r, kwargs=%r)' % (cn, self.func, self.args, self.kwargs)


def _is_spec(obj, strict=False):
    # a little util for codifying the spec type checking in glom
    if isinstance(obj, TType):
        return True
    if strict:
        return type(obj) is Spec
    # TODO: revisit line below
    return callable(getattr(obj, 'glomit', None)) and not isinstance(obj, type)  # pragma: no cover


class Invoke(object):
    """Specifier type designed for easy invocation of callables from glom.

    Args:
      func (callable): A function or other callable object.

    ``Invoke`` is similar to :func:`functools.partial`, but with the
    ability to set up a "templated" call which interleaves constants and
    glom specs.

    For example, the following creates a spec which can be used to
    check if targets are integers:

    >>> is_int = Invoke(isinstance).specs(T).constants(int)
    >>> glom(5, is_int)
    True

    And this composes like any other glom spec:

    >>> target = [7, object(), 9]
    >>> glom(target, [is_int])
    [True, False, True]

    Another example, mixing positional and keyword arguments:

    >>> spec = Invoke(sorted).specs(T).constants(key=int, reverse=True)
    >>> target = ['10', '5', '20', '1']
    >>> glom(target, spec)
    ['20', '10', '5', '1']

    Invoke also helps with evaluating zero-argument functions:

    >>> glom(target={}, spec=Invoke(int))
    0

    (A trivial example, but from timestamps to UUIDs, zero-arg calls do come up!)

    .. note::

       ``Invoke`` is mostly for functions, object construction, and callable
       objects. For calling methods, consider the :attr:`~glom.T` object.

    """
    def __init__(self, func):
        if not callable(func) and not _is_spec(func, strict=True):
            raise TypeError('expected func to be a callable or Spec instance,'
                            ' not: %r' % (func,))
        self.func = func
        self._args = ()
        # a registry of every known kwarg to its freshest value as set
        # by the methods below. the **kw dict is used as a unique marker.
        self._cur_kwargs = {}

    @classmethod
    def specfunc(cls, spec):
        """Creates an :class:`Invoke` instance where the function is
        indicated by a spec.

        >>> spec = Invoke.specfunc('func').constants(5)
        >>> glom({'func': range}, (spec, list))
        [0, 1, 2, 3, 4]

        """
        return cls(Spec(spec))

    def constants(self, *a, **kw):
        """Returns a new :class:`Invoke` spec, with the provided positional
        and keyword argument values stored for passing to the
        underlying function.

        >>> spec = Invoke(T).constants(5)
        >>> glom(range, (spec, list))
        [0, 1, 2, 3, 4]

        Subsequent positional arguments are appended:

        >>> spec = Invoke(T).constants(2).constants(10, 2)
        >>> glom(range, (spec, list))
        [2, 4, 6, 8]

        Keyword arguments also work as one might expect:

        >>> round_2 = Invoke(round).constants(ndigits=2).specs(T)
        >>> glom(3.14159, round_2)
        3.14

        :meth:`~Invoke.constants()` and other :class:`Invoke`
        methods may be called multiple times, just remember that every
        call returns a new spec.
        """
        ret = self.__class__(self.func)
        ret._args = self._args + ('C', a, kw)
        ret._cur_kwargs = dict(self._cur_kwargs)
        ret._cur_kwargs.update({k: kw for k, _ in kw.items()})
        return ret

    def specs(self, *a, **kw):
        """Returns a new :class:`Invoke` spec, with the provided positional
        and keyword arguments stored to be interpreted as specs, with
        the results passed to the underlying function.

        >>> spec = Invoke(range).specs('value')
        >>> glom({'value': 5}, (spec, list))
        [0, 1, 2, 3, 4]

        Subsequent positional arguments are appended:

        >>> spec = Invoke(range).specs('start').specs('end', 'step')
        >>> target = {'start': 2, 'end': 10, 'step': 2}
        >>> glom(target, (spec, list))
        [2, 4, 6, 8]

        Keyword arguments also work as one might expect:

        >>> multiply = lambda x, y: x * y
        >>> times_3 = Invoke(multiply).constants(y=3).specs(x='value')
        >>> glom({'value': 5}, times_3)
        15

        :meth:`~Invoke.specs()` and other :class:`Invoke`
        methods may be called multiple times, just remember that every
        call returns a new spec.
        """
        ret = self.__class__(self.func)
        ret._args = self._args + ('S', a, kw)
        ret._cur_kwargs = dict(self._cur_kwargs)
        ret._cur_kwargs.update({k: kw for k, _ in kw.items()})
        return ret

    def star(self, args=None, kwargs=None):
        """Returns a new :class:`Invoke` spec, with *args* and/or *kwargs*
        specs set to be "starred" or "star-starred" (respectively)

        >>> import os.path
        >>> spec = Invoke(os.path.join).star(args='path')
        >>> target = {'path': ['path', 'to', 'dir']}
        >>> glom(target, spec)
        'path/to/dir'

        Args:
           args (spec): A spec to be evaluated and "starred" into the
              underlying function.
           kwargs (spec): A spec to be evaluated and "star-starred" into
              the underlying function.

        One or both of the above arguments should be set.

        The :meth:`~Invoke.star()`, like other :class:`Invoke`
        methods, may be called multiple times. The *args* and *kwargs*
        will be stacked in the order in which they are provided.
        """
        if args is None and kwargs is None:
            raise TypeError('expected one or both of args/kwargs to be passed')
        ret = self.__class__(self.func)
        ret._args = self._args + ('*', args, kwargs)
        ret._cur_kwargs = dict(self._cur_kwargs)
        return ret

    def __repr__(self):
        chunks = [self.__class__.__name__]
        fname_map = {'C': 'constants', 'S': 'specs', '*': 'star'}
        if type(self.func) is Spec:
            chunks.append('.specfunc({!r})'.format(self.func.spec))
        else:
            chunks.append('({!r})'.format(self.func))
        for i in range(len(self._args) // 3):
            op, args, kwargs = self._args[i * 3: i * 3 + 3]
            fname = fname_map[op]
            chunks.append('.{}('.format(fname))
            if op in ('C', 'S'):
                chunks.append(', '.join(
                    [repr(a) for a in args] +
                    ['{}={!r}'.format(k, v) for k, v in kwargs.items()
                     if self._cur_kwargs[k] is kwargs]))
            else:
                if args:
                    chunks.append('args=' + repr(args))
                if args and kwargs:
                    chunks.append(", ")
                if kwargs:
                    chunks.append('kwargs=' + repr(kwargs))
            chunks.append(')')
        return ''.join(chunks)

    def glomit(self, target, scope):
        all_args = []
        all_kwargs = {}

        recurse = lambda spec: scope[glom](target, spec, scope)
        func = recurse(self.func) if _is_spec(self.func, strict=True) else self.func

        for i in range(len(self._args) // 3):
            op, args, kwargs = self._args[i * 3: i * 3 + 3]
            if op == 'C':
                all_args.extend(args)
                all_kwargs.update({k: v for k, v in kwargs.items()
                                   if self._cur_kwargs[k] is kwargs})
            elif op == 'S':
                all_args.extend([recurse(arg) for arg in args])
                all_kwargs.update({k: recurse(v) for k, v in kwargs.items()
                                   if self._cur_kwargs[k] is kwargs})
            elif op == '*':
                if args is not None:
                    all_args.extend(recurse(args))
                if kwargs is not None:
                    all_kwargs.update(recurse(kwargs))

        return func(*all_args, **all_kwargs)


class TType(object):
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
        return _t_child(self, '[', item)

    def __call__(self, *args, **kwargs):
        return _t_child(self, '(', (args, kwargs))

    def __repr__(self):
        t_path = _T_PATHS[self]
        return _format_t(t_path[1:], t_path[0])

    def __getstate__(self):
        t_path = _T_PATHS[self]
        return tuple(('T' if t_path[0] is T else 'S',) + t_path[1:])

    def __setstate__(self, state):
        _T_PATHS[self] = (T if state[0] == 'T' else S,) + state[1:]


_T_PATHS = weakref.WeakKeyDictionary()


def _t_child(parent, operation, arg):
    t = TType()
    _T_PATHS[t] = _T_PATHS[parent] + (operation, arg)
    return t


def _t_eval(target, _t, scope):
    t_path = _T_PATHS[_t]
    i = 1
    if t_path[0] is T:
        cur = target
    elif t_path[0] is S:
        cur = scope
    else:
        raise ValueError('TType instance with invalid root object')
    while i < len(t_path):
        op, arg = t_path[i], t_path[i + 1]
        if type(arg) in (Spec, TType, Literal):
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
            get = scope[TargetRegistry].get_handler('get', cur, path=t_path[2:i+2:2])
            try:
                cur = get(cur, arg)
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


T = TType()  # target aka Mr. T aka "this"
S = TType()  # like T, but means grab stuff from Scope, not Target

_T_PATHS[T] = (T,)
_T_PATHS[S] = (S,)
UP = make_sentinel('UP')
ROOT = make_sentinel('ROOT')


def _format_invocation(name='', args=(), kwargs=None):  # pragma: no cover
    # TODO: add to boltons
    kwargs = kwargs or {}
    a_text = ', '.join([repr(a) for a in args])
    if isinstance(kwargs, dict):
        kwarg_items = kwargs.items()
    else:
        kwarg_items = kwargs
    kw_text = ', '.join(['%s=%r' % (k, v) for k, v in kwarg_items])

    star_args_text = a_text
    if star_args_text and kw_text:
        star_args_text += ', '
    star_args_text += kw_text

    return '%s(%s)' % (name, star_args_text)


class Let(object):
    """
    This specifier type assigns variables to the scope.

    >>> target = {'data': {'val': 9}}
    >>> spec = (Let(value=T['data']['val']), {'val': S['value']})
    >>> glom(target, spec)
    {'val': 9}
    """
    def __init__(self, **kw):
        if not kw:
            raise TypeError('expected at least one keyword argument')
        self._binding = kw

    def glomit(self, target, scope):
        scope.update({
            k: scope[glom](target, v, scope) for k, v in self._binding.items()})
        return target

    def __repr__(self):
        cn = self.__class__.__name__
        return _format_invocation(cn, kwargs=self._binding)


def _format_t(path, root=T):
    def kwarg_fmt(kw):
        if isinstance(kw, str):
            return kw
        return repr(kw)
    prepr = ['T' if root is T else 'S']
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


class CheckError(GlomError):
    """This :exc:`GlomError` subtype is raised when target data fails to
    pass a :class:`Check`'s specified validation.

    An uncaught ``CheckError`` looks like this::

       >>> target = {'a': {'b': 'c'}}
       >>> glom(target, {'b': ('a.b', Check(type=int))})
       Traceback (most recent call last):
       ...
       CheckError: target at path ['a.b'] failed check, got error: "expected type to be 'int', found type 'str'"

    If the ``Check`` contains more than one condition, there may be
    more than one error message. The string rendition of the
    ``CheckError`` will include all messages.

    You can also catch the ``CheckError`` and programmatically access
    messages through the ``msgs`` attribute on the ``CheckError``
    instance.

    .. note::

       As of 2018-07-05 (glom v18.2.0), the validation subsystem is
       still very new. Exact error message formatting may be enhanced
       in future releases.

    """
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

    If any check condition fails, a :class:`~glom.CheckError` is raised.

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

    Aside from *spec*, all arguments are keyword arguments. Each
    argument, except for *default*, represent a check
    condition. Multiple checks can be passed, and if all check
    conditions are left unset, Check defaults to performing a basic
    truthy check on the value.

    """
    # TODO: the next level of Check would be to play with the Scope to
    # allow checking to continue across the same level of
    # dictionary. Basically, collect as many errors as possible before
    # raising the unified CheckError.
    def __init__(self, spec=T, **kwargs):
        self.spec = spec
        self._orig_kwargs = dict(kwargs)
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

    def glomit(self, target, scope):
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
                    if type(e) is self._ValidationError:
                        if self.default is not RAISE:
                            return self.default
                    else:
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

    def __repr__(self):
        cn = self.__class__.__name__
        posargs = (self.spec,) if self.spec is not T else ()
        return format_invocation(cn, posargs, self._orig_kwargs)


class Auto(object):
    """
    Switch to Auto mode (the default)

    TODO: this seems like it should be a sub-class of class Spec() --
    if Spec() could help define the interface for new "modes" or dialects
    that would also help make match mode feel less duct-taped on
    """
    def __init__(self, spec=None):
        self.spec = spec

    def glomit(self, target, scope):
        scope[MODE] = _glom_auto
        return scope[glom](target, self.spec, scope)

    def __repr__(self):
        cn = self.__class__.__name__
        rpr = '' if self.spec is None else repr(self.spec)
        return '%s(%s)' % (cn, rpr)



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
def _handle_dict(target, spec, scope):
    ret = type(spec)()  # TODO: works for dict + ordereddict, but sufficient for all?
    for field, subspec in spec.items():
        val = scope[glom](target, subspec, scope)
        if val is SKIP:
            continue
        if type(field) in (Spec, TType):
            field = scope[glom](target, field, scope)
        ret[field] = val
    return ret


def _handle_list(target, spec, scope):
    subspec = spec[0]
    iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])
    try:
        iterator = iterate(target)
    except Exception as e:
        raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                        % (target.__class__.__name__, Path(*scope[Path]), e))
    ret = []
    base_path = scope[Path]
    for i, t in enumerate(iterator):
        scope[Path] = base_path + [i]
        val = scope[glom](t, subspec, scope)
        if val is SKIP:
            continue
        if val is STOP:
            break
        ret.append(val)
    return ret


def _handle_tuple(target, spec, scope):
    res = target
    for subspec in spec:
        nxt = scope[glom](res, subspec, scope)
        if nxt is SKIP:
            continue
        if nxt is STOP:
            break
        res = nxt
        # this makes it so that specs in a tuple effectively nest.
        scope = scope[LAST_CHILD_SCOPE]
        if not isinstance(subspec, list):
            scope[Path] += [getattr(subspec, '__name__', subspec)]
    return res


class TargetRegistry(object):
    '''
    responsible for registration of target types for iteration
    and attribute walking
    '''
    def __init__(self, register_default_types=True):
        self._op_type_map = {}
        self._op_type_tree = {}  # see _register_fuzzy_type for details

        self._op_auto_map = OrderedDict()  # op name to function that returns handler function

        self._register_builtin_ops()

        if register_default_types:
            self._register_default_types()
        return

    def get_handler(self, op, obj, path=None, raise_exc=True):
        """for an operation and object **instance**, obj, return the
        closest-matching handler function, raising UnregisteredTarget
        if no handler can be found for *obj* (or False if
        raise_exc=False)

        """
        ret = False
        obj_type = type(obj)
        type_map = self.get_type_map(op)
        if type_map:
            try:
                ret = type_map[obj_type]
            except KeyError:
                type_tree = self._op_type_tree.get(op, {})
                closest = self._get_closest_type(obj, type_tree=type_tree)
                if closest is None:
                    ret = False
                else:
                    ret = type_map[closest]

        if ret is False and raise_exc:
            raise UnregisteredTarget(op, obj_type, type_map=type_map, path=path)

        return ret

    def get_type_map(self, op):
        try:
            return self._op_type_map[op]
        except KeyError:
            return OrderedDict()

    def _get_closest_type(self, obj, type_tree):
        default = None
        for cur_type, sub_tree in type_tree.items():
            if isinstance(obj, cur_type):
                sub_type = self._get_closest_type(obj, type_tree=sub_tree)
                ret = cur_type if sub_type is None else sub_type
                return ret
        return default

    def _register_default_types(self):
        self.register(object)
        self.register(dict, get=operator.getitem)
        self.register(list, get=_get_sequence_item)
        self.register(tuple, get=_get_sequence_item)
        self.register(_AbstractIterable, iterate=iter)

    def _register_fuzzy_type(self, op, new_type, _type_tree=None):
        """Build a "type tree", an OrderedDict mapping registered types to
        their subtypes

        The type tree's invariant is that a key in the mapping is a
        valid parent type of all its children.

        Order is preserved such that non-overlapping parts of the
        subtree take precedence by which was most recently added.
        """
        if _type_tree is None:
            try:
                _type_tree = self._op_type_tree[op]
            except KeyError:
                _type_tree = self._op_type_tree[op] = OrderedDict()

        registered = False
        for cur_type, sub_tree in list(_type_tree.items()):
            if issubclass(cur_type, new_type):
                sub_tree = _type_tree.pop(cur_type)  # mutation for recursion brevity
                try:
                    _type_tree[new_type][cur_type] = sub_tree
                except KeyError:
                    _type_tree[new_type] = OrderedDict({cur_type: sub_tree})
                registered = True
            elif issubclass(new_type, cur_type):
                _type_tree[cur_type] = self._register_fuzzy_type(op, new_type, _type_tree=sub_tree)
                registered = True
        if not registered:
            _type_tree[new_type] = OrderedDict()
        return _type_tree

    def register(self, target_type, **kwargs):
        if not isinstance(target_type, type):
            raise TypeError('register expected a type, not an instance: %r' % (target_type,))
        exact = kwargs.pop('exact', None)
        new_op_map = dict(kwargs)

        for op_name in sorted(set(self._op_auto_map.keys()) | set(new_op_map.keys())):
            cur_type_map = self._op_type_map.setdefault(op_name, OrderedDict())

            if op_name in new_op_map:
                handler = new_op_map[op_name]
            elif target_type in cur_type_map:
                handler = cur_type_map[target_type]
            else:
                try:
                    handler = self._op_auto_map[op_name](target_type)
                except Exception as e:
                    raise TypeError('error while determining support for operation'
                                    ' "%s" on target type: %s (got %r)'
                                    % (op_name, target_type.__name__, e))
            if handler is not False and not callable(handler):
                raise TypeError('expected handler for op "%s" to be'
                                ' callable or False, not: %r' % (op_name, handler))
            new_op_map[op_name] = handler

        for op_name, handler in new_op_map.items():
            self._op_type_map[op_name][target_type] = handler

        if not exact:
            for op_name in new_op_map:
                self._register_fuzzy_type(op_name, target_type)

        return

    def register_op(self, op_name, auto_func=None, exact=False):
        """add operations beyond the builtins ('get' and 'iterate' at the time
        of writing).

        auto_func is a function that when passed a type, returns a
        handler associated with op_name if it's supported, or False if
        it's not.

        See glom.core.register_op() for the global version used by
        extensions.
        """
        if not isinstance(op_name, basestring):
            raise TypeError('expected op_name to be a text name, not: %r' % (op_name,))
        if auto_func is None:
            auto_func = lambda t: False
        elif not callable(auto_func):
            raise TypeError('expected auto_func to be callable, not: %r' % (auto_func,))

        # determine support for any previously known types
        known_types = set(sum([list(m.keys()) for m
                               in self._op_type_map.values()], []))
        type_map = self._op_type_map.get(op_name, OrderedDict())
        type_tree = self._op_type_tree.get(op_name, OrderedDict())
        for t in known_types:
            if t in type_map:
                continue
            try:
                handler = auto_func(t)
            except Exception as e:
                raise TypeError('error while determining support for operation'
                                ' "%s" on target type: %s (got %r)'
                                % (op_name, t.__name__, e))
            if handler is not False and not callable(handler):
                raise TypeError('expected handler for op "%s" to be'
                                ' callable or False, not: %r' % (op_name, handler))
            type_map[t] = handler

        if not exact:
            for t in known_types:
                self._register_fuzzy_type(op_name, t, _type_tree=type_tree)

        self._op_type_map[op_name] = type_map
        self._op_type_tree[op_name] = type_tree
        self._op_auto_map[op_name] = auto_func

    def _register_builtin_ops(self):
        def _get_iterable_handler(type_obj):
            return iter if callable(getattr(type_obj, '__iter__', None)) else False

        self.register_op('iterate', _get_iterable_handler)
        self.register_op('get', lambda _: getattr)


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
        Inspect: kwargs.pop('inspector', None),
        MODE: _glom_auto,
    })
    scope[UP] = scope
    scope[ROOT] = scope
    scope[T] = target
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
    parent = scope
    scope = scope.new_child()
    parent[LAST_CHILD_SCOPE] = scope
    scope[T] = target
    scope[Spec] = spec
    scope[UP] = parent

    if isinstance(spec, TType):  # must go first, due to callability
        return _t_eval(target, spec, scope)
    elif callable(getattr(spec, 'glomit', None)):
        return spec.glomit(target, scope)

    return scope[MODE](target, spec, scope)


def _glom_auto(target, spec, scope):
    if isinstance(spec, dict):
        return _handle_dict(target, spec, scope)
    elif isinstance(spec, list):
        return _handle_list(target, spec, scope)
    elif isinstance(spec, tuple):
        return _handle_tuple(target, spec, scope)
    elif isinstance(spec, basestring):
        return Path.from_text(spec).glomit(target, scope)
    elif callable(spec):
        return spec(target)

    raise TypeError('expected spec to be dict, list, tuple, callable, string,'
                    ' or other Spec-like type, not: %r' % (spec,))


_DEFAULT_SCOPE.update({
    glom: _glom,
    TargetRegistry: TargetRegistry(register_default_types=True),
})


def register(target_type, **kwargs):
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
    _DEFAULT_SCOPE[TargetRegistry].register(target_type, **kwargs)
    return


def register_op(op_name, **kwargs):
    """For extension authors needing to add operations beyond the builtin
    'get' and 'iterate' to the default scope. See TargetRegistry for more details.
    """
    _DEFAULT_SCOPE[TargetRegistry].register_op(op_name, **kwargs)
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
    def __init__(self, **kwargs):
        register_default_types = kwargs.pop('register_default_types', True)
        scope = kwargs.pop('scope', _DEFAULT_SCOPE)

        # this "freezes" the scope in at the time of construction
        self.scope = ChainMap(dict(scope))
        self.scope[TargetRegistry] = TargetRegistry(register_default_types=register_default_types)

    def register(self, target_type, **kwargs):
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
        exact = kwargs.pop('exact', False)
        self.scope[TargetRegistry].register(target_type, exact=exact, **kwargs)
        return

    def glom(self, target, spec, **kwargs):
        return glom(target, spec, scope=self.scope, **kwargs)


class Fill(object):
    """A specifier type which switches to glom into "fill-mode". For the
    spec contained within the Fill, glom will only interpret explicit
    specifier types (including T objects). Whereas the default mode
    has special interpretations for each of these builtins, fill-mode
    takes a lighter touch, making Fill great for "filling out" Python
    literals, like tuples, dicts, sets, and lists.

    >>> target = {'data': [0, 2, 4]}
    >>> spec = Fill((T['data'][2], T['data'][0]))
    >>> glom(target, spec)
    (4, 0)

    As you can see, glom's usual built-in tuple item chaining behavior
    has switched into a simple tuple constructor.

    (Sidenote for Lisp fans: Fill is like glom's quasi-quoting.)

    """
    def __init__(self, spec=None):
        self.spec = spec

    def glomit(self, target, scope):
        scope[MODE] = _fill
        return scope[glom](target, self.spec, scope)

    def fill(self, target):
        return glom(target, self)

    def __repr__(self):
        cn = self.__class__.__name__
        rpr = '' if self.spec is None else repr(self.spec)
        return '%s(%s)' % (cn, rpr)


def _fill(target, spec, scope):
    # TODO: register an operator or two for the following to allow
    # extension. This operator can probably be shared with the
    # upcoming traversal/remap feature.
    recurse = lambda val: scope[glom](target, val, scope)
    if type(spec) is dict:
        return {recurse(key): recurse(val) for key, val in spec.items()}
    if type(spec) in (list, tuple, set, frozenset):
        result = [recurse(val) for val in spec]
        if type(spec) is list:
            return result
        return type(spec)(result)
    if callable(spec):
        return spec(target)
    return spec
