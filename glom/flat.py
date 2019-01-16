
from boltons.typeutils import make_sentinel

from .core import TargetRegistry, Path

_MISSING = make_sentinel('_MISSING')


class Sum(object):
    def __init__(self, default=None):
        self.default = default

    def glomit(self, target, scope):
        ret = _MISSING

        iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])

        try:
            iterator = iterate(target)
        except Exception as e:
            raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                            % (target.__class__.__name__, Path(*scope[Path]), e))

        for val in iterator:
            if ret is _MISSING:
                ret = type(val)()
                continue
            ret += val
        if ret is _MISSING:
            return self.default
        return ret
