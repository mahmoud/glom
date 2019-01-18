
import operator
import itertools

from boltons.typeutils import make_sentinel

from .core import TargetRegistry, Path, T, glom

_MISSING = make_sentinel('_MISSING')


class Fold(object):
    def __init__(self, subspec, start, op=operator.iadd):
        self.subspec = subspec
        self.start = start
        self.op = op
        if not callable(op):
            raise TypeError()
        if not callable(start):
            raise TypeError()

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
        ret, op = self.start(), self.op

        for v in iterator:
            ret = op(ret, v)

        return ret


    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, start=%r, op=%r)' % (cn, self.subspec, self.start, self.op)


class Sum(Fold):
    def __init__(self, subspec=T, start=int):
        super(Sum, self).__init__(subspec=subspec, start=start, op=operator.iadd)

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, start=%r)' % (cn, self.subspec, self.start)


class Flatten(Fold):
    def __init__(self, subspec=T, start=list, lazy=False):
        super(Flatten, self).__init__(subspec=subspec, start=start, op=operator.iadd)
        self.lazy = lazy

    def _fold(self, iterator):
        if self.lazy:
            return itertools.chain(iterator)
        return super(Flatten, self)._fold(iterator)
