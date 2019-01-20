
import operator
import itertools

from boltons.typeutils import make_sentinel

from .core import TargetRegistry, Path, T, glom, GlomError, UnregisteredTarget

_MISSING = make_sentinel('_MISSING')


class FoldError(GlomError):
    """Error raised when Fold() is called on non-iterable
    targets, and possibly other uses in the future."""
    pass


class Fold(object):
    """The `Fold` specifier type is glom's building block for reducing
    iterables in data, implementing the classic `fold
    <https://en.wikipedia.org/wiki/Fold_(higher-order_function)>`_
    from functional programming, similar to Python's built-in
    :func:`reduce`.

    Args:
       subspec: A spec representing the target to fold, which must be
          an iterable, or otherwise registered to 'iterate' (with
          :func:`~glom.register`).
       init (callable): A function or type which will be invoked to
          initialize the accumulator value.
       op (callable): A function to call on the accumulator value and
          every value, the result of which will become the new
          accumulator value. Defaults to :func:`operator.iadd`.

    Usage is as follows:

       >>> target = [set([1, 2]), set([3]), set([2, 4])]
       >>> result = glom(target, Fold(T, init=frozenset, op=frozenset.union))
       >>> result == frozenset([1, 2, 3, 4])
       True

    Note the required ``spec`` and ``init`` arguments. ``op`` is
    optional, but here must be used because the :type:`set` and
    :type:`frozenset` types do not work with addition.

    While :type:`~glom.Fold` is powerful, :type:`~glom.Flatten` and
    :type:`~glom.Sum` are subtypes with more convenient defaults for
    day-to-day use.
    """
    def __init__(self, subspec, init, op=operator.iadd):
        self.subspec = subspec
        self.init = init
        self.op = op
        if not callable(op):
            raise TypeError('expected callable for %s op param, not: %r' %
                            (self.__class__.__name__, op))
        if not callable(init):
            raise TypeError('expected callable for %s init param, not: %r' %
                            (self.__class__.__name__, op))

    def glomit(self, target, scope):
        if self.subspec is not T:
            target = scope[glom](target, self.subspec, scope)

        try:
            iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])
        except UnregisteredTarget as ut:
            raise FoldError('can only %s on iterable targets, not %s type (%s)'
                            % (self.__class__.__name__, type(target).__name__, ut))

        try:
            iterator = iterate(target)
        except Exception as e:
            # TODO: should this be a GlomError of some form? probably
            # not, because it was registered, but an unexpected
            # failure occurred.
            raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                            % (target.__class__.__name__, Path(*scope[Path]), e))

        return self._fold(iterator)

    def _fold(self, iterator):
        ret, op = self.init(), self.op

        for v in iterator:
            ret = op(ret, v)

        return ret

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, init=%r, op=%r)' % (cn, self.subspec, self.init, self.op)


class Sum(Fold):
    """The `Sum` specifier type is used to aggregate integers and other
    numericals using addition, much like the :func:`sum()` builtin.

    >>> glom(range(5), Sum())
    10

    To "sum" lists and other iterables, see the :class:`Flatten`
    spec. For other objects, see the :class:`Fold` specifier type.
    """
    def __init__(self, subspec=T, init=int):
        super(Sum, self).__init__(subspec=subspec, init=init, op=operator.iadd)

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, init=%r)' % (cn, self.subspec, self.init)


class Flatten(Fold):
    """The `Flatten` specifier type is used to combine iterables. By
    default it flattens an iterable of iterables into a single list
    containing items from all iterables.

    >>> target = [[1], [2, 3]]
    >>> glom(target, Flatten())
    [1, 2, 3]

    You can also set the *lazy* flag to ``True``, which defers the
    iteration and returns a generator instead. Use this to avoid
    making extra lists during intermediate processing steps.
    """
    def __init__(self, subspec=T, init=list):
        if init == 'lazy':
            self.lazy = True
            init = list
        else:
            self.lazy = False
        super(Flatten, self).__init__(subspec=subspec, init=init, op=operator.iadd)

    def _fold(self, iterator):
        if self.lazy:
            return itertools.chain.from_iterable(iterator)
        return super(Flatten, self)._fold(iterator)

    def __repr__(self):
        cn = self.__class__.__name__
        if self.lazy:
            return '%s(%r, init="lazy")' % (cn, self.subspec)
        return '%s(%r, init=%r)' % (cn, self.subspec, self.init)


def flatten(target, **kwargs):
    """The ``flatten()`` function is a convenient wrapper around the
    :class:`Flatten` specifier type.

    ``flatten()`` turns an iterable of iterables into a single list,
    but it has a few arguments which give it more power:

    Args:

       init (callable): A function or type which gives the initial
          value of the return. The value must support addition. Common
          values might be :type:`list` (the default), :type:`tuple`,
          or even :type:`int`. You can also pass ``init="lazy"`` to
          get a generator.
       levels (int): A positive integer representing the number of
          nested levels to flatten. Defaults to 1.
       spec: The glomspec to fetch before flattening. This defaults to the
          the root level of the object.

    Usage is straightforward.

      >>> target = [[1, 2], [3], [4]]
      >>> flatten(target)
      [1, 2, 3, 4]

    Because integers support addition, we actually have two levels of flattening possible:

      >>> flatten(target, init=int, levels=2)
      10

    However flattening an integer itself will raise an exception:

      >>> target = 3
      >>> flatten(target)
      Traceback (most recent call last):
      ...
      FoldError: can only Flatten on iterable targets, not int type (...)

    By default, ``flatten()`` will add a mix of iterables together,
    making it a more-robust alternative to the built-in
    ``sum(list_of_iterables, [])`` trick most experienced Python
    programmers are familiar with using:

      >>> list_of_iterables = [range(2), [2, 3], (4, 5)]
      >>> sum(list_of_iterables, [])
      Traceback (most recent call last):
      ...
      TypeError: can only concatenate list (not "tuple") to list

    Whereas flatten() handles this just fine:

      >>> flatten(list_of_iterables)
      [0, 1, 2, 3, 4, 5]

    For more involved flattening, see the :class:`Flatten` and
    :class:`Fold` specifier types.

    """
    subspec = kwargs.pop('spec', T)
    init = kwargs.pop('init', list)
    levels = kwargs.pop('levels', 1)
    if kwargs:
        raise TypeError('unexpected keyword args: %r' % sorted(kwargs.keys()))

    if levels == 0:
        return target
    if levels < 0:
        raise ValueError('expected levels >= 0, not %r' % levels)
    spec = (subspec,)
    spec += (Flatten(init="lazy"),) * (levels - 1)
    spec += (Flatten(init=init),)

    return glom(target, spec)
