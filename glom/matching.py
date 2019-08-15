"""
Contains code associated with implementing match specs

match mode tends to build expression trees by conjoining
together matches with And / &, Or / |

a "mode" provides new definitions for the meaning of
basic python data structures inside the glom spec

example use cases:

filter list on condition (e.g. >= 10)
[Coalesce(Match(int & (M >= 10)), default=SKIP)]

ensure that dictionary values are all strings
Match({DEFAULT: str})

2 syntaxes for combining expressions:

And(int, M > 0)
M & int & (M > 0)

"""
from __future__ import unicode_literals

import sys

from boltons.typeutils import make_sentinel

from .core import GlomError, glom, T, Spec


class GlomMatchError(GlomError): pass
class GlomTypeMatchError(GlomMatchError, TypeError): pass


class Match(object):
    """
    switch to "match" mode
    """
    def __init__(self, spec):
        self.spec = spec

    def glomit(self, target, scope):
        scope[glom] = _glom_match
        return scope[glom](target, self.spec, scope)


DEFAULT = make_sentinel("DEFAULT")
DEFAULT.__doc__ = """
DEFAULT is used to represent keys that are not otherwise matched
in a dict in match mode
"""
DEFAULT.glomit = lambda target, scope: target


class _Bool(object):
    """
    abstract class for binary operations
    """
    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)


class And(_Bool):
    def __init__(self, *children):
        self.children = children

    def glomit(self, target, scope):
        # all children must match without exception
        for child in self.children:
            target = scope[glom](target, child, scope)
        return target

    def __repr__(self):
        return "(" + ") & (".join([repr(c) for c in self.children]) + ")"


class Or(_Bool):
    def __init__(self, *children):
        self.children = children

    def glomit(self, target, scope):
        for child in self.children[:-1]:
            try:  # one child must match without exception
                return scope[glom](target, child, scope)
            except GlomError:
                pass
        return scope[glom](target, self.children[-1], scope)

    def __repr__(self):
        return "(" + ") | (".join([repr(c) for c in self.children]) + ")"


class MType(object):
    """
    Similar to T, but for matching

    M == is an escape valve for comparisons with values that would otherwise
    be interpreted as specs by Match
    """
    def __init__(self, lhs, op, rhs):
        self.lhs, self.op, self.rhs = lhs, op, rhs

    def __eq__(self, other):
        return MType(self, '=', other)

    def __gt__(self, other):
        return MType(self, '>', other)

    def __lt__(self, other):
        return MType(self, '<', other)

    def __and__(self, other):
        if self is M:
            return And(other)
        return And(self, other)

    __rand__ = __and__

    def __or__(self, other):
        if self is M:
            return Or(other)
        return Or(self, other)

    # TODO: straightforward to extend this to all comparisons

    def glomit(self, target, scope):
        lhs, op, rhs = self.lhs, self.op, self.rhs
        if lhs is M:
            lhs = target
        if rhs is M:
            rhs = target
        if op == '=':
            if lhs == rhs:
                pass
            else:
                raise GlomMatchError("{!r} != {!r}".format(lhs, rhs))
        elif op == '>':
            if lhs > rhs:
                pass
            else:
                raise GlomMatchError("{!r} > {!r}".format(lhs, rhs))
        return target

    def __repr__(self):
        if self is M:
            return "M"
        op = self.op
        if op == '=':
            op = '=='
        return "{!r} {} {!r}".format(self.lhs, op, self.rhs)


M = MType(None, None, None)


def _precedence(match):
    """
    in a dict spec, target-keys may match many
    spec-keys (e.g. 1 will match int, M > 0, and 1);
    therefore we need a precedence for which order to try
    keys in; higher = later
    """
    if match is DEFAULT:
        return 5
    if type(match) in (list, tuple, set, frozenset, dict):
        return 4
    if isinstance(match, type):
        return 3
    if hasattr(match, "glomit"):
        return 2
    if callable(match):
        return 1
    return 0  # == match


def _handle_dict(target, spec, scope):
    if not isinstance(target, dict):
        raise GlomTypeMatchError(type(target), dict)
    spec_keys = spec  # cheating a little bit here, list-vs-dict, but saves an object copy sometimes
    if sys.version_info < (3, 6):
        # apply a deterministic precedence if the python version itself does not guarantee ordering
        spec_keys = sorted(spec_keys, key=_precedence)
    for key, val in target.items():
        for spec_key in spec_keys:
            try:
                _glom_match(key, spec_key, scope)
            except GlomMatchError:
                pass
            else:
                _glom_match(val, spec[spec_key], scope)
                break
        else:
            raise GlomMatchError("key {!r} didn't match any of {!r}".format(key, spec_keys))
    return target


def _glom_match(target, spec, scope):
    scope = scope.new_child()
    scope[T] = target
    scope[Spec] = spec

    if callable(getattr(spec, 'glomit', None)):
        return spec.glomit(target, scope)
    elif isinstance(spec, type):
        if not isinstance(target, spec):
            raise GlomTypeMatchError(type(target), spec)
    elif isinstance(spec, dict):
        return _handle_dict(target, spec, scope)
    elif isinstance(spec, (list, set, frozenset)):
        if not isinstance(target, type(spec)):
            raise GlomTypeMatchError(type(target), type(spec))
        for item in target:
            last_error = None
            for child in spec:
                try:
                    _glom_match(item, child, scope)
                    break
                except GlomMatchError as e:
                    last_error = e
            else:  # did not break, something went wrong
                if target and not spec:
                    raise GlomMatchError("{!r} does not match empty {}".format(
                        target, type(spec).__name__))
                raise last_error
        return target
    elif isinstance(spec, tuple):
        if not isinstance(target, tuple):
            raise GlomTypeMatchError(type(target), tuple)
        if len(target) != len(spec):
            raise GlomMatchError("{!r} does not match {!r}".format(target, spec))
        for sub_target, sub_spec in zip(target, spec):
            _glom_match(sub_target, sub_spec, scope)
        return target
    if isinstance(spec, type):
        if not isinstance(target, spec):
            raise GlomTypeMatchError(type(target), spec)
        return target

    if target != spec:
        raise GlomMatchError("{!r} does not match {!r}".format(target, spec))

