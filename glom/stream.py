"""
Helpers for streaming use cases -- that is, specifier types which yield their
results incrementally so that they can be applied to targets which
are themselves streaming (e.g. chunks of rows from a database, lines
from a file) without excessive memory usage.
"""
from __future__ import unicode_literals

from itertools import chain

from boltons.iterutils import split_iter

from .core import glom, T, STOP, SKIP, Check, _MISSING, Path, TargetRegistry, Call
from .reduction import Flatten

"""
itertools to add:

* filter
* map
* zip
* takewhile / dropwhile
* split
* chunked
* windowed
* unique

(Iter(T.items)
 .filter(T.is_activated)
 .map(fetch_from_db))

(Iter((T.items, Check(T.is_activated, default=SKIP), fetch_from_db)))

# should there be a .first() or something?
"""

class Iter(object):
    """``Iter()`` is glom's counterpart to the built-in :func:`iter()`
    function. Given an iterable target, yields the result of applying
    the passed spec to each element of the target. Basically, a lazy
    version of the default list-spec behavior.

    ``Iter()`` also respects glom's :data:`~glom.SKIP` and
    :data:`~glom.STOP` singletons for filtering and breaking
    iteration.

    Args:

       subspec: A subspec to be applied on each element from the iterable.
       sentinel: Keyword-only argument, which, when found in the
         iterable stream, causes the iteration to stop. Same as with the
         built-in :func:`iter`.

    >>> glom(['1', '2', '1', '3'], (Iter(int), set, tuple))
    (1, 2, 3)


    """
    def __init__(self, subspec=T, **kwargs):
        self.subspec = subspec if type(subspec) is tuple else (subspec,)
        self._spec_stack = kwargs.pop('spec_stack', [])

        self.sentinel = kwargs.pop('sentinel', STOP)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % sorted(kwargs))
        return

    def glomit(self, target, scope):
        for iter_spec in self._spec_stack:
            target = scope[glom](target, iter_spec, scope)

        iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])
        try:
            iterator = iterate(target)
        except Exception as e:
            raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                            % (target.__class__.__name__, Path(*scope[Path]), e))

        for i, sub in enumerate(iterator):
            yld = scope[glom](sub, self.subspec, scope.new_child({Path: scope[Path] + [i]}))
            if yld is SKIP:
                continue
            elif yld is STOP:
                return
            yield yld
        return

    def filter(self, subspec):
        # if falsey, skip
        # TODO: gotta fix handle_tuple and SKIP interaction if this is gonna work
        return Iter(Check(subspec, default=SKIP))

    def map(self, subspec):
        return Iter(subspec=self.subspec + (subspec,), sentinel=self.sentinel)

    def zip(self, subspec, otherspec, fill_value=_MISSING):
        return

    def windowed(self, subspec):
        return

    def split(self, sep=None, maxsplit=None):
        _split_iter = Call(split_iter, args=(T,), kwargs={'sep': sep, 'maxsplit': maxsplit})
        # the sentinel is kind of meaningless here, but the intention is that it'll carry through for future chaining
        return Iter(spec_stack=self._spec_stack + [_split_iter, self])

    def chain(self):
        # like sum but lazy, target presumed to be an iterable of iterables
        return Iter(spec_stack=self._spec_stack + [Flatten(init='lazy')])  # Call(chain.from_iterable, args=(T,))])


class Pipe(object):
    # Iter is the streaming dual of []
    # Pipe is the streaming dual of ()
    pass


class Partial(object):
    """
    makes "upgrading" arbitrary python functions into
    glom specs more convenient, so that itertools, toolz, et al
    may be more easily integrated into streaming glom chains
    """
    def __init__(self, func, *a, **kw):
        self.func = func
        self.args = (a, kw)

    def __call__(self, *a, **kw):
        ret = Partial(self.func)
        ret.args = self.args + (a, kw)
        return ret

    def glomit(self, target, scope):
        all_args = []
        all_kwargs = {}
        recurse = lambda spec: scope[glom](target, spec, scope)
        for i in range(len(self.args) // 2):
            args = self.args[i * 2]
            kwargs = self.args[i * 2 + 1]
            if i % 2:
                # odd arg-sets are literals
                all_args.extend(args)
                all_kwargs.update(kwargs)
            else:
                # even arg-sets are specs
                all_args.extend([recurse(arg) for arg in args])
                # TODO: detect "overwritten" kwargs and avoid computing
                all_kwargs.update({k: recurse(v) for k, v in kwargs.items()})
        return self.func(*all_args, **all_kwargs)
