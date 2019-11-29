"""
this module contains helpers for building glom data
structure stack traces from glom scopes

there are a few cursors that are extracted from each level of the
scope; these cursors say which path down from a target and spec
was being processed

scope[Path] -- target cursor
scope[SCOPE_POS] -- spec cursor (for dict + tuple type specs)
"""
from __future__ import print_function

from .core import Spec, T, UP, Path, SPEC_POS, TType


_NO_TARGET = object()


def line_stack(scope):
    """
    unpack a scope into a single line summary
    (shortest summary possible)
    """
    # root glom call generates two scopes up at the top that aren't part
    # of execution
    scopes = list(reversed(scope.maps[:-2]))

    # the goal here is to do a kind of delta-compression --
    # if the target is the same, don't repeat it
    segments = []
    target = _NO_TARGET
    for scope in scopes:
        spec = scope[Spec]
        target, prev_target = scope[T], target
        segments.append('/')
        if type(spec) in (TType, Path):
            segments.append(repr(spec))
        else:
            segments.append(type(spec).__name__)
        if target != prev_target:
            segments.append('!')
            segments.append(type(target).__name__)
        if Path in scope:
            segments.append('<')
            segments.append('->'.join([str(p) for p in scope[Path]]))
            segments.append('>')

    return "".join(segments)


def short_stack(scope):
    """
    unpack a scope into a multi-line but short summary
    """
    pass


def tall_stack(scope):
    """
    unpack a scope into the most detailed information
    """
    pass


"""
# doodling around with a glom spec to help with generating traces
# for dogfooding purposes; not QUITE there, but very close
_STACK_SPEC = Ref("Seg",
    {
        'spec': T[Spec],
        'target': T[T],
        'target_pos': Or(T[Path], SKIP),
        'spec_pos': Or(T[SPEC_POS], SKIP),
        'parent': Or(And(M(T[Spec]) != T, (T[Spec], Ref("Seg"))), SKIP),
    })


_STACK_UNWIND = (
    Let(stack=[]),
    Ref('scope', (
        S['stack'].append(T),
    )),
    S['stack'],
    reversed
)
"""
