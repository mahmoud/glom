"""
Group mode
"""
from boltons.typeutils import make_sentinel

from .core import glom, MODE


ACC = make_sentinel('ACC')
ACC.__doc__ = """
current accumulator for aggregation
"""


ACC2 = make_sentinel('ACC2')
ACC2.__doc__ = """
supporting accumulators for aggregation

e.g. if current aggregation is average,
the supporting data structure would be (sum, count)
"""


class Group(object):
    def __init__(self, spec):
        self.spec = spec

    def glomit(self, target, scope):
        scope[MODE] = _group
        if type(self.spec) is list:
            scope[ACC] = []
        elif type(self.spec) is dict:
            scope[ACC] = {}
        scope[ACC2] = {}
        for t in target:
            ret = scope[glom](t, self.spec, scope)
        return ret


def _group(target, spec, scope):
    """
    Group mode dispatcher
    """
    recurse = lambda spec: scope[glom](target, spec, scope)
    acc = scope[ACC]  # current accumulator
    acc2 = scope[ACC2]  # current acuumulator support structure
    if type(spec) is dict:
        for keyspec, valspec in spec.items():
            key = recurse(keyspec)
            if key not in acc:
                acc[key] = _mk_acc(valspec)
                acc2[key] = {}
            scope[ACC] = acc[key]
            scope[ACC2] = acc2[key]
            acc[key] = recurse(valspec)
        return acc
    elif type(spec) is list:
        for valspec in spec:
            acc.append(recurse(valspec))
        return acc
    elif callable(spec):
        return spec(target)
    raise TypeError("not a valid spec")


def _mk_acc(spec):
    """
    make an acculumator for a given spec
    """
    if type(spec) is dict:
        return {}
    if type(spec) is list:
        return []


class First(object):
    def __init__(self): pass

    def glomit(self, target, scope):
        if ACC2 not in scope:
            raise Exception("called outside of aggregation scope")
        acc2 = scope[ACC2]
        if self not in acc2:
            acc2[self] = target
        return acc2[self]
