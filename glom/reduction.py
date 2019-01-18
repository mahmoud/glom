
import operator
import itertools

from boltons.typeutils import make_sentinel

from .core import TargetRegistry, Path, T, glom

_MISSING = make_sentinel('_MISSING')


class Fold(object):
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

        iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])

        try:
            iterator = iterate(target)
        except Exception as e:
            # TODO: should this be a GlomError of some form?
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
    def __init__(self, subspec=T, init=list, lazy=False):
        super(Flatten, self).__init__(subspec=subspec, init=init, op=operator.iadd)
        self.lazy = lazy

    def _fold(self, iterator):
        if self.lazy:
            return itertools.chain.from_iterable(iterator)
        return super(Flatten, self)._fold(iterator)

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, init=%r, lazy=%r)' % (cn, self.subspec, self.init, self.lazy)
