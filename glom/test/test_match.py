import json

import pytest

from glom import glom, S, Literal, T
from glom.matching import Match, M, GlomMatchError, And, Or, DEFAULT, Optional, Required
from glom.core import Build, SKIP


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
    glom(1.0, M >= 1)
    glom(1.0, M < 2)
    glom(1.0, M <= 1)
    glom(1.0, M != None)
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
    glom({None: 1}, Match({DEFAULT: object}))
    _chk(Match((int, str)), (1, "cat"), (1, 2))
    with pytest.raises(GlomMatchError):
        glom({1: 2}, Match({(): int}))
    with pytest.raises(GlomMatchError):
        glom(1, Match({}))


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


def test_pattern_matching():
    pattern_matcher = (
        M & Match(1) & Literal('one') |
        M & Match(2) & Literal('two') |
        M & Match(float) & Literal('float')
        )
    assert glom(1, pattern_matcher) == 'one'
    assert glom(1.1, pattern_matcher) == 'float'

    # obligatory fibonacci

    fib = (M > 2) & (lambda n: glom(n - 1, fib) + glom(n - 2, fib)) | T

    assert glom(5, fib) == 8


def test_examples():
    assert glom(8, (M > 7) & Literal(7)) == 7
    assert glom(range(10), [(M > 7) & Literal(7) | T]) == [0, 1, 2, 3, 4, 5, 6, 7, 7, 7]
    assert glom(range(10), [(M > 7) & Literal(SKIP) | T]) == [0, 1, 2, 3, 4, 5, 6, 7]

def test_reprs():
    repr(M)
    repr(M == 1)
    repr(M | M == 1)
    repr(M & M == 1)


def test_sample():
    """
    test meant to cover a more realistic use
    """
    import datetime

    data = {
        'name': 'item',
        'date_added': datetime.datetime.now(),
        'desc': 'a data item',
        'tags': ['data', 'new'],
    }

    spec = Match({
        'name': str,
        Optional('date_added'): datetime.datetime,
        'desc': str,
        'tags': [str,]})

    def good():
        glom(data, spec)
    def bad():
        with pytest.raises(GlomMatchError):
            glom(data, spec)

    good()  # should match
    del data['date_added']
    good()  # should still match w/out optional
    del data['desc']
    bad()
    data['desc'] = 'a data item'
    data['extra'] = 'will fail on extra'
    bad()
    spec.spec[str] = str  # now extra str-key/str-val are okay
    good()
    data['extra2'] = 2  # but extra str-key/non-str-val are bad
    bad()
    # reset data
    data = {
        'name': 'item',
        'date_added': datetime.datetime.now(),
        'desc': 'a data item',
        'tags': ['data', 'new'],
    }
    del spec.spec[str]
    spec.spec[Required(str)] = str  # now there MUST be at least one str
    bad()
    data['extra'] = 'extra'
    good()


def test_ternary():
    assert glom('abc', Match(Or(None, 'abc'))) == 'abc'


def test_sky():
    """test adapted from github.com/shopkick/opensky"""

    def as_type(sub_schema, typ):
        'after checking sub_schema, pass the result to typ()'
        return And(sub_schema, Build(typ))

    assert glom('abc', as_type(M == 'abc', list)) == list('abc')

    def none_or(sub_schema):
        'allow None or sub_schema'
        return Match(Or(None, sub_schema))

    assert glom(None, none_or('abc')) == None
    assert glom('abc', none_or('abc')) == 'abc'
    with pytest.raises(GlomMatchError):
        glom(123, none_or('abc'))

    def in_range(sub_schema, _min, _max):
        'check that sub_schema is between _min and _max'
        return Match(And(sub_schema, _min < M, M < _max))
        # TODO: make _min < M < _max work

    assert glom(1, in_range(int, 0, 2))
    with pytest.raises(GlomMatchError):
        glom(-1, in_range(int, 0, 2))
