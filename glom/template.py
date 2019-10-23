"""
template mode is for building python literals,
similar to quasi-quoting in lisp
"""
from glom import glom, MODE


class Template(object):
    def __init__(self, spec):
        self.spec = spec

    def glomit(self, target, scope):
        scope[MODE] = _template
        return scope[glom](target, self.spec, scope)


def _template(target, spec, scope):
    recurse = lambda val: scope[glom](target, val, scope)
    if type(spec) is dict:
        return {recurse(key): recurse(val) for key, val in spec.items()}
    if type(spec) in (list, tuple, set, frozenset):
        result = [recurse(val) for val in spec]
        if type(spec) is list:
            return result
        return type(spec)(result)
    if callable(spec):
        return spec(target)
    return spec
