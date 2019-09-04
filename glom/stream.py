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
