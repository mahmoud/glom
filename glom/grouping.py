"""
Group mode
"""
from boltons.typeutils import make_sentinel

from .core import glom, MODE

ACC = make_sentinel('ACC')
ACC.__doc__ = """
current accumulator for aggregation
"""

NXT_ACC = make_sentinel('ACC')
NXT_ACC.__doc__ = """
next accumulator for aggregation
"""


class Group(object):
    def __init__(self, spec):
        self.spec = spec

    def glomit(self, target, scope):
        scope[MODE] = _group
        scope[NXT_ACC] = type(self.spec)()  # dict or list
        for t in target:
            scope[glom](t, self.spec, scope)
        return scope[NXT_ACC]


def _group(target, spec, scope):
    """
    Group mode dispatcher
    """
    recurse = lambda spec: scope[glom](target, spec, scope)
    acc = scope[ACC] = scope[NXT_ACC]  # current accumulator
    if type(spec) is dict:
        for keyspec, valspec in spec.items():
            key = recurse(keyspec)
            if key not in acc:
                acc[key] = _mk_acc(valspec)
            scope[NXT_ACC] = acc[key]
            recurse(valspec)
    elif type(spec) is list:
        for valspec in spec:
            acc.append(recurse(valspec))
    elif callable(spec):
        return spec(target)


def _mk_acc(spec):
    """
    make an acculumator for a given spec
    """
    if type(spec) is dict:
        return {}
    if type(spec) is list:
        return []

# need a function which grabs the parent spec and introspects
# -- how to make a new child?

# come to think of it -- a dict is the only key which is valid

