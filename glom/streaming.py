"""
Helpers for streaming use cases -- that is, specifier types which yield their
results incrementally so that they can be applied to targets which
are themselves streaming (e.g. chunks of rows from a database, lines
from a file) without excessive memory usage.
"""
from __future__ import unicode_literals

from itertools import islice, dropwhile
from functools import partial
try:
    from itertools import izip, izip_longest
except ImportError:
    izip = zip  # py3
    from itertools import zip_longest as izip_longest

from boltons.iterutils import split_iter, chunked_iter, windowed_iter, unique_iter

from .core import glom, T, STOP, SKIP, Check, _MISSING, Path, TargetRegistry, Call, Spec, S
from .reduction import Flatten

"""
itertools to add:

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
        self.subspec = subspec
        self._spec_stack = kwargs.pop('spec_stack', [])

        self.sentinel = kwargs.pop('sentinel', STOP)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % sorted(kwargs))
        return

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, spec_stack=%r)' % (cn, self.subspec, self._spec_stack)

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

    def map(self, subspec):
        """Return a new Iter() spec which will apply the provided subspec to
        each element of the iterable.

        Because a spec can be a callable, this functions as the
        equivalent of the built-in :func:`map` in Python 3, but with
        the full power of glom specs.
        """
        return Iter(subspec, spec_stack=[self])

    def filter(self, subspec):
        """Return a new Iter() spec which will skip over elements matching the
        given subspec.

        Because a spec can be a callable, this functions as the
        equivalent of the built-in :func:`filter` in Python 3, but with
        the full power of glom specs.
        """
        # TODO: invert kwarg for itertools.filterfalse
        return Iter(spec_stack=[self, Iter(Check(subspec, default=SKIP))])

    def chunked(self, size, fill=_MISSING):
        """Return a new Iter() spec which groups elements in the iterable
        into lists of length *size*.

        If the optional *fill* argument is provided, iterables not
        evenly divisible by *size* will be padded out by the *fill*
        constant. Otherwise, the final chunk will be shorter than *size*.

        >>> list(glom(range(10), Iter().chunked(3)))
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        >>> list(glom(range(10), Iter().chunked(3, fill=None)))
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]
        """
        kw = {'size': size}
        if fill is not _MISSING:
            kw['fill'] = fill
        _chunked_iter = Call(chunked_iter, args=(T,), kwargs=kw)
        return Iter(spec_stack=[self, _chunked_iter])

    def windowed(self, size):
        """Return a new Iter() spec which will yield a sliding window of
        adjacent elements in the iterable. Each tuple yielded will be
        of length *size*.

        Useful for getting adjacent pairs and triples.

        >>> list(glom(range(4), Iter().windowed(2)))
        [(0, 1), (1, 2), (2, 3)]
        """
        _windowed_iter = Call(windowed_iter, args=(T,), kwargs={'size': size})
        return Iter(spec_stack=[self, _windowed_iter])

    def unique(self, subspec=None):
        """Return a new Iter() spec which lazily filters out duplicate
        values, i.e., only the first appearance of a value in a stream will
        be yielded.

        >>> target = list('gloMolIcious')
        >>> out = list(glom(target, Iter().unique(T.lower())))
        >>> ''.join(out)
        u'gloMIcus'

        """
        if not subspec:
            _unique_iter = Call(unique_iter, args=(T,))
        else:
            spec_glom = Spec(Call(partial, args=(Spec(subspec).glom,), kwargs={'scope': S}))
            _unique_iter = Call(unique_iter, args=(T, spec_glom))
        return Iter(spec_stack=[self, _unique_iter])

    def split(self, sep=None, maxsplit=None):
        _split_iter = Call(split_iter, args=(T,), kwargs={'sep': sep, 'maxsplit': maxsplit})
        return Iter(spec_stack=[_split_iter, self])

    def chain(self):
        # like sum but lazy, target presumed to be an iterable of iterables
        return Iter(spec_stack=[self, Flatten(init='lazy')])

    def slice(self, *a):
        # TODO: make a kwarg-compatible version of this (islice takes no kwargs)
        _slice_iter = Call(islice, args=(T,) + a)
        return Iter(spec_stack=[_slice_iter, self])

    def limit(self, count):
        return self.slice(count)

    def zip(self, spec=T, otherspec=T, fill=_MISSING):
        _zip, kw = izip, {}
        if fill is not _MISSING:
            _zip = izip_longest
            kw['fillvalue'] = fill
        _zip_iter = Call(_zip, args=(spec, otherspec), kwargs=kw)
        return Iter(spec_stack=[_zip_iter, self])

    def takewhile(self, subspec):
        return Iter(Check(subspec, default=STOP), spec_stack=[self])

    def dropwhile(self, subspec):
        spec_glom = Spec(Call(partial, args=(Spec(subspec).glom,), kwargs={'scope': S}))
        _dropwhile_iter = Call(dropwhile, args=(spec_glom, T))
        return Iter(spec_stack=[self, _dropwhile_iter])


class Pipe(object):
    # Iter is the streaming dual of []
    # Pipe is the streaming dual of ()
    pass
