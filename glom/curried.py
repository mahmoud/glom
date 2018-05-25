from glom.core import glom as __glom
import functools

__all__ = ['glom']

__glom_rv = lambda v, spec: __glom(spec, v)


def glom(spec):
    return functools.partial(__glom_rv, spec)
