"""
Helpers for streaming use cases -- that is, specifier types which yield their
results incrementally so that they can be applied to targets which
are themselves streaming (e.g. chunks of rows from a database, lines
from a file) without excessive memory usage.
"""
from __future__ import unicode_literals

from itertools import islice, dropwhile, takewhile
import inspect
from functools import partial, wraps
try:
    from itertools import izip, izip_longest, imap
except ImportError:
    izip = zip  # py3
    imap = map
    ifilter = filter
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
        self._iter_stack = kwargs.pop('_iter_stack', [])

        self.sentinel = kwargs.pop('sentinel', STOP)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % sorted(kwargs))
        return

    def __repr__(self):
        cn = self.__class__.__name__
        chunks = [self.__class__.__name__]
        if self.subspec != T:
            chunks.append('({!r})'.format(self.subspec))
        else:
            chunks.append('()')
        for fname, args, callback in reversed(self._iter_stack):
            meth = getattr(self, fname)
            arg_names, _, _, _ = inspect.getargspec(meth)
            arg_names = arg_names[1:]  # get rid of self
            # TODO: something fancier with defaults:
            chunks.append("." + fname)
            if len(args) == 0:
                chunks.append("()")
            elif len(arg_names) == 1:
                assert len(args) == 1
                chunks.append('({!r})'.format(args[0]))
            else:
                chunks.append('({})'.format(", ".join([
                    '{}={!r}'.format(name, val) for name, val in zip(arg_names, args)])))
        return ''.join(chunks)

    def glomit(self, target, scope):
        iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])
        try:
            iterator = iterate(target)
        except Exception as e:
            raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                            % (target.__class__.__name__, Path(*scope[Path]), e))

        for fname, args, callback in reversed(self._iter_stack):
            iterator = callback(iterator, scope)

        return iter(iterator)

    def _add_op(self, opname, args, callback):
        return type(self)(_iter_stack=[(opname, args, callback)] + self._iter_stack)

    def map(self, subspec):
        """Return a new Iter() spec which will apply the provided subspec to
        each element of the iterable.

        Because a spec can be a callable, this functions as the
        equivalent of the built-in :func:`map` in Python 3, but with
        the full power of glom specs.
        """
        # whatever validation you want goes here
        # TODO: DRY the self._add_op with a decorator?
        return self._add_op(
            'map',
            (subspec,),
            lambda iterable, scope: imap(
                lambda t: scope[glom](t, subspec, scope), iterable))

    def filter(self, subspec):
        """Return a new Iter() spec which will include only elements matching the
        given subspec.

        Because a spec can be a callable, this functions as the
        equivalent of the built-in :func:`filter` in Python 3, but with
        the full power of glom specs.
        """
        # TODO: invert kwarg for itertools.filterfalse
        return self._add_op(
            'filter',
            (subspec,),
            lambda iterable, scope: ifilter(
                lambda t: scope[glom](t, Check(spec, default=SKIP), scope), iterable))

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
        args = size,
        if fill is not _MISSING:
            kw['fill'] = fill
            args += (fill,)
        return self._add_op(
            'chunked', args, lambda it, scope: chunked_iter(it, **kw))

    '''  # TODO: port over to new pattern
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

    def zip(self, spec=T, otherspec=T, fill=_MISSING):
        _zip, kw = izip, {}
        if fill is not _MISSING:
            _zip = izip_longest
            kw['fillvalue'] = fill
        _zip_iter = Call(_zip, args=(spec, otherspec), kwargs=kw)
        return Iter(spec_stack=[_zip_iter, self])
    '''

    def slice(self, *a):
        # TODO: make a kwarg-compatible version of this (islice takes no kwargs)
        try:
            islice([], *a)
        except TypeError:
            raise TypeError('invalid slice arguments: %r' % (a,))
        return self._add_op('slice', a, lambda it, scope: islice(it, *a))

    def limit(self, count):
        return self.slice(count)

    def takewhile(self, subspec):
        return self._add_op(
            'takewhile',
            (subspec,),
            lambda it, scope: takewhile(
                lambda t: scope[glom](t, subspec, scope), it))

    def dropwhile(self, subspec):
        return self._add_op(
            'dropwhile',
            (subspec,),
            lambda it, scope: dropwhile(
                lambda t: scope[glom](t, subspec, scope), it))
