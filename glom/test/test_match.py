import json

import pytest

from glom import glom
from glom.matching import Match, M, GlomMatchError, And, Or
from glom.core import Build


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
    glom(1.0, M & (M > 0) & float)
    glom(1.0, M | (M > 100) | float)
    # test idiom for enum
    with pytest.raises(GlomMatchError):
        glom("c", Match("a"))
    with pytest.raises(GlomMatchError):
        glom("c", Match(Or("a", "b")))
    _chk(Match(M | "a" | "b"), "a", "c")


def test_cruddy_json():
    _chk(
        Match({'int_id?': M & Build(int) & (M > 0)}),
        {'int_id?': '1'},
        {'int_id?': '-1'})
    # embed a build
    squished_json = Match({
        'smooshed_json': M & Build(json.loads) & {
            'sub': M & Build(json.loads) & 1 }
        })
    glom({'smooshed_json': json.dumps({'sub': json.dumps(1)})}, squished_json)


def pattern_matching_experiment():
    pattern_matcher = (M &
        Match(1) & 'one' |
        Match(2) & 'two' |
        Match(float) & 'float'
        )
    assert glom.glom(1, pattern_matcher) == 'one'
    assert glom.glom(1.1, pattern_matcher) == 'float'
