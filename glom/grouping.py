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
    """
    supports nesting grouping operations --
    think of a glom-style recursive boltons.iterutils.bucketize

    the "branches" of a Group spec are dicts;
    the leaves are lists, or an Aggregation object
    an Aggregation object is any object that defines the
    method agg(target, accumulator)

    target is the current target, accumulator is a dict
    maintained by Group mode
    """
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
    acc2 = scope[ACC2]  # current acuumulator support structure
    if callable(getattr(spec, "agg", None)):
        return spec.agg(target, acc2)
    if type(spec) is dict:
        acc = scope[ACC]  # current accumulator
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
        acc = scope[ACC]  # current accumulator
        for valspec in spec:
            assert type(valspec) is not dict
            # dict inside list is not valid
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
    return None


class First(object):
    __slots__ = ()

    def agg(self, target, acc2):
        if self not in acc2:
            acc2[self] = target
        return acc2[self]


class Avg(object):
    __slots__ = ()

    def agg(self, target, acc2):
        if self not in acc2:
            acc2[self] = [0, 0.0]
        acc2[self][0] += target
        acc2[self][1] += 1
        return acc2[self][0] / acc2[self][1]


class Sum(object):
    __slots__ = ()

    def agg(self, target, acc2):
        if self not in acc2:
            acc2[self] = 0
        acc2[self] += target
        return acc2[self]
