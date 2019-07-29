import pytest

from glom import glom
from glom.matching import Match, M, GlomMatchError, And, Or


def _chk(spec, good_target, bad_target):
    glom(good_target, spec)
    with pytest.raises(GlomMatchError):
        glom(bad_target, spec)

def test():
    _chk(Match(1), 1, 2)
    _chk(Match(int), 1, 1.0)
    # test unordered sequence comparisons
    _chk(Match([int]), [1], ["1"])
    _chk(Match({int}), {1}, [1])
    _chk(Match(frozenset({float})), frozenset({}), frozenset({"1"}))
    with pytest.raises(GlomMatchError):
        glom([1], Match([]))  # empty shouldn't match
    glom({"a": 1, "b": 2}, Match({str: int}))
    glom(2, M == 2)
    glom(int, M == int)
    glom(1.0, M > 0)
    glom(1.0, (M > 0) & float)
    glom(1.0, (M > 100) | float)
    glom(1.0, And & (M > 0) & float)
    glom(1.0, Or | (M > 100) | float)
    glom(1.0, M & (M > 0) & float)
    glom(1.0, M | (M > 100) | float)
