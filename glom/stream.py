"""
Helpers for streaming use cases -- that is, specifier types which yield their
results incrementally so that they can be applied to targets which
are themselves streaming (e.g. chunks of rows from a database, lines
from a file) without excessive memory usage.
"""
from __future__ import unicode_literals

from .core import glom, T, STOP, SKIP


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

    >>> glom("123123", (Iter(int), set, tuple))
    (1, 2, 3)


    """
    def __init__(self, subspec=T, **kwargs):
        self.subspec = subspec
        self.sentinel = kwargs.pop('sentinel', STOP)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % sorted(kwargs))
        return

    def glomit(self, target, scope):
        iterator = iter(target)
        for sub in iterator:
            yld = scope[glom](sub, self.subspec, scope)
            if yld is SKIP:
                continue
            elif yld is STOP:
                return
            yield yld
        return


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
        for i in range(len(self.args) / 2):
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
