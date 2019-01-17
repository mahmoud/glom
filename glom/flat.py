
from boltons.typeutils import make_sentinel

from .core import TargetRegistry, Path, T, glom

_MISSING = make_sentinel('_MISSING')

# TODO: Sum, Flatten, and Reduce


class Sum(object):
    def __init__(self, subspec=T, start=0):
        self.subspec = subspec
        self.start = start

    def glomit(self, target, scope):
        ret = self.start

        if self.subspec is not T:
            target = scope[glom](target, self.subspec, scope)

        iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])

        try:
            iterator = iterate(target)
        except Exception as e:
            # TODO: should this be a GlomError of some form?
            raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                            % (target.__class__.__name__, Path(*scope[Path]), e))

        for v in iterator:
            ret += v
        return ret
