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

from .core import Spec, T, UP, Path, TType


_NO_TARGET = object()


def _unpack_stack(scope):
    """
    convert scope to [(scope, spec, target)]
    """
    # root glom call generates two scopes up at the top that aren't part
    # of execution
    return [(scope, scope[Spec], scope[T]) for scope in list(reversed(scope.maps[:-2]))]


# TODO: get fancier here and replace repr()
# with something that only recurses one level
def _format_value(value, maxlen):
    s = repr(value)
    if len(s) > maxlen:
        s = s[:maxlen] + '...'
    return s


def line_stack(scope):
    """
    unpack a scope into a single line summary
    (shortest summary possible)
    """
    # the goal here is to do a kind of delta-compression --
    # if the target is the same, don't repeat it
    segments = []
    prev_target = _NO_TARGET
    for scope, spec, target in _unpack_stack(scope):
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
        prev_target = target

    return "".join(segments)


def short_stack(scope, width=110):
    """
    unpack a scope into a multi-line but short summary
    """
    segments = []
    prev_target = _NO_TARGET
    target_width = width - len("   target: ")
    spec_width = width - len("   spec: ")
    for scope, spec, target in _unpack_stack(scope):
        if target != prev_target:
            segments.append("   target: "+ _format_value(target, target_width))
        prev_target = target
        segments.append("   spec: " + _format_value(spec, spec_width))
    return "\n".join(segments)


def tall_stack(scope):
    """
    unpack a scope into the most detailed information
    """
    segments = []
    prev_target = _NO_TARGET
    for scope, spec, target in _unpack_stack(scope):
        if target != prev_target:
            segments.append("   target: "+ repr(target))
        prev_target = target
        segments.append("   spec: " + repr(spec))
    return "\n".join(segments)


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

TODO: in the future consider having a handle for SPECs to dump their state


SPEC_POS = make_sentinel('SPEC_POS')
SPEC_POS.__doc__ = '''
``SPEC_POS`` is used to keep track of the current position
within a spec -- e.g. key of dict, index of tuple -- for
the purposes of debugging
'''

"""
