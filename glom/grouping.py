"""
Group mode
"""
from boltons.typeutils import make_sentinel

from .core import glom, MODE, SKIP, STOP, TargetRegistry, Path


ACC_TREE = make_sentinel('ACC_TREE')
ACC_TREE.__doc__ = """
tree of accumulators for aggregation;
structure roughly corresponds to the result,
but is not 1:1; instead the main purpose is to ensure
data is kept until the Group() finishes executing
"""

CUR_AGG = make_sentinel('CUR_AGG')
CUR_AGG.__doc__ = """
the spec which is currently performing aggregation --
useful for specs that want to work in either "aggregate"
mode, or "spec" mode depending on if they are in Group mode
or not; this sentinel in the Scope allows a spec to decide
if it is "closest" to the Group and so should behave
like an aggregate, or if it is further away and so should
have normal spec behavior.
"""


def target_iter(target, scope):
    iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])

    try:
        iterator = iterate(target)
    except Exception as e:
        # TODO: should this be a GlomError of some form? probably
        # not, because it was registered, but an unexpected
        # failure occurred.
        raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                        % (target.__class__.__name__, Path(*scope[Path]), e))
    return iterator


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

    unlike Iter(), Group() converts an iterable target
    into a single result; Iter() converts an iterable
    target into an iterable result
    """
    def __init__(self, spec):
        self.spec = spec

    def glomit(self, target, scope):
        scope[MODE] = GROUP
        scope[CUR_AGG] = None  # reset aggregation tripwire for sub-specs
        scope[ACC_TREE] = {}
        ret = None
        for t in target_iter(target, scope):
            last, ret = ret, scope[glom](t, self.spec, scope)
            if ret is STOP:
                return last
        return ret


def GROUP(target, spec, scope):
    """
    Group mode dispatcher; also sentinel for current mode = group
    """
    recurse = lambda spec: scope[glom](target, spec, scope)
    tree = scope[ACC_TREE]  # current acuumulator support structure
    if callable(getattr(spec, "agg", None)):
        return spec.agg(target, tree)
    elif callable(spec):
        return spec(target)
    if type(spec) not in (dict, list):
        raise TypeError("not a valid spec")
    if id(spec) in tree:
        acc = tree[id(spec)]  # current accumulator
    else:
        acc = tree[id(spec)] = type(spec)()
    if type(spec) is dict:
        done = True
        for keyspec, valspec in spec.items():
            if tree.get(keyspec, None) is STOP:
                continue
            key = recurse(keyspec)
            if key is SKIP:
                done = False  # SKIP means we still want more vals
                continue
            if key is STOP:
                tree[keyspec] = STOP
                continue
            if key not in acc:
                # TODO: guard against key == id(spec)
                tree[key] = {}
            scope[ACC_TREE] = tree[key]
            result = recurse(valspec)
            if result is STOP:
                tree[keyspec] = STOP
                continue
            done = False  # SKIP or returning a value means we still want more vals
            if result is not SKIP:
                acc[key] = result
        if done:
            return STOP
        return acc
    elif type(spec) is list:
        for valspec in spec:
            assert type(valspec) is not dict
            # dict inside list is not valid
            result = recurse(valspec)
            if result is STOP:
                return STOP
            if result is not SKIP:
                acc.append(result)
        return acc
    raise ValueError("{} not a valid spec type for Group mode".format(type(spec)))


class First(object):
    """
    holds onto the first value

    >>> glom([1, 2, 3], Group(First()))
    1
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree:
            tree[self] = STOP
            return target
        return STOP


class Avg(object):
    """
    takes the numerical average of all values;
    raises exception on non-numeric value

    >>> glom([1, 2, 3], Group(Avg()))
    2.0
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree:
            tree[self] = [0, 0.0]
        tree[self][0] += target
        tree[self][1] += 1
        return tree[self][0] / tree[self][1]


class Sum(object):
    """
    takes the sum of all values;
    raises exception on values incompatible with addition operator

    >>> glom([1, 2, 3], Group(Sum()))
    6
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree:
            tree[self] = 0
        tree[self] += target
        return tree[self]


class Max(object):
    """
    takes the maximum of all values;
    raises exception on values that are not comparable

    >>> glom([1, 2, 3], Group(Max()))
    3
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree:
            tree[self] = target
        if target > tree[self]:
            tree[self] = target
        return tree[self]


class Min(object):
    """
    takes the minimum of all values;
    raises exception on values that are not comparable

    >>> glom([1, 2, 3], Group(Min()))
    1
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree:
            tree[self] = target
        if target < tree[self]:
            tree[self] = target
        return tree[self]


class Count(object):
    """
    takes a count of how many values occurred

    >>> glom([1, 2, 3], Group(Count()))
    3
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree:
            tree[self] = 0
        tree[self] += 1
        return tree[self]


'''
NOTE: this cannot be done as an aggregator since they are
not recursive; enable when recursion is available again
once grouping / reduction merge is complete

class Limit(object):
    """
    limits the number of values passed to sub-accumulator

    >>> glom([1, 2, 3], Group(T))
    3
    >>> glom([1, 2, 3], Group(Limit(1, T)))
    1
    """
    __slots__ = ('n', 'agg')

    def __init__(self, n, agg):
        self.n, self.agg = n, agg

    def agg(self, target, tree):
        if self not in tree:
            tree[self] = 0
        tree[self] += 1
        if tree[self] > self.n:
            return STOP
        return self.agg.agg(target, tree)
'''
