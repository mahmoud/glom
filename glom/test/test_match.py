import json

import pytest

from glom import glom, S, Literal, T, Merge, Fill, Let, Ref
from glom.matching import (
    Match, M, GlomMatchError, GlomTypeMatchError, And, Or, Not,
    DEFAULT, Optional, Required, Regex)
from glom.core import Auto, SKIP, Ref


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
    # test idiom for enum
    with pytest.raises(GlomMatchError):
        glom("c", Match("a"))
    glom("c", Not(Match("a")))
    with pytest.raises(GlomMatchError):
        glom("c", Match(Or("a", "b")))
    _chk(Match(Or("a", "b")), "a", "c")
    glom({None: 1}, Match({DEFAULT: object}))
    _chk(Match((int, str)), (1, "cat"), (1, 2))
    with pytest.raises(GlomMatchError):
        glom({1: 2}, Match({(): int}))
    with pytest.raises(GlomMatchError):
        glom(1, Match({}))
    Match(M > 0).verify(1.0)


def test_spec_match():
    """test that M __call__ can be used to wrap a subspec for comparison"""
    target = {}
    target['a'] = target
    assert glom(target, M == M('a'))
    

def test_cruddy_json():
    _chk(
        Match({'int_id?': Auto((int, (M > 0)))}),
        {'int_id?': '1'},
        {'int_id?': '-1'})
    # embed a build
    squished_json = Match({
        'smooshed_json': Auto(
            (json.loads, Match({
                'sub': Auto((json.loads, M == 1))})))
        })
    glom({'smooshed_json': json.dumps({'sub': json.dumps(1)})}, squished_json)


def test_pattern_matching():
    pattern_matcher = Or(
        And(Match(1), Literal('one')),
        And(Match(2), Literal('two')),
        And(Match(float), Literal('float'))
        )
    assert glom(1, pattern_matcher) == 'one'
    assert glom(1.1, pattern_matcher) == 'float'

    # obligatory fibonacci

    fib = (M > 2) & (lambda n: glom(n - 1, fib) + glom(n - 2, fib)) | T

    assert glom(5, fib) == 8

    factorial = (
        lambda t: t + 1, Ref('fact', (
            lambda t: t - 1,
            (M == 0) & Fill(1) |
            (Let(r=Ref('fact')),
                S, lambda s: s['r'] * s[T]))))

    assert glom(4, factorial) == 4 * 3 * 2


def test_examples():
    assert glom(8, (M > 7) & Literal(7)) == 7
    assert glom(range(10), [(M > 7) & Literal(7) | T]) == [0, 1, 2, 3, 4, 5, 6, 7, 7, 7]
    assert glom(range(10), [(M > 7) & Literal(SKIP) | T]) == [0, 1, 2, 3, 4, 5, 6, 7]

def test_reprs():
    repr(M)
    repr(M == 1)
    repr(M | M == 1)
    repr(M & M == 1)
    repr(~M)
    repr(And(1, 2))
    repr(Or(1, 2))
    repr(Not(1))
    repr(GlomMatchError("uh oh"))
    repr(GlomTypeMatchError("uh oh {0}", dict))
    assert repr(And(M == 1, float)) == "(M == 1) & float"
    assert repr(eval(repr(And(M == 1, float)))) == "(M == 1) & float"


def test_shortcircuit():
    assert glom(False, Fill(M | "default")) == "default"
    assert glom(True, Fill(M | "default")) == True
    assert glom(True, Fill(M & "default")) == "default"
    with pytest.raises(GlomMatchError):
        glom(False, Fill(M & "default"))
    assert glom(False, ~M) == False
    assert glom(True, Fill(~M | "default")) == "default"


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


def test_regex():
    assert glom('abc', (Regex('(?P<test>.*)'), S['test'])) == 'abc'
    with pytest.raises(GlomMatchError):
        glom(1, Regex('1'))


def test_ternary():
    assert glom('abc', Match(Or(None, 'abc'))) == 'abc'


def test_sky():
    """test adapted from github.com/shopkick/opensky"""

    def as_type(sub_schema, typ):
        'after checking sub_schema, pass the result to typ()'
        return And(sub_schema, Auto(typ))

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

    def default_if_none(sub_schema, default_factory):
        return Or(
            And(M == None, Auto(lambda t: default_factory())), sub_schema)

    assert glom(1, default_if_none(T, list)) == 1
    assert glom(None, default_if_none(T, list)) == []

    def nullable_list_of(*items):
        return default_if_none(Match(list(items)), list)

    assert glom(None, nullable_list_of(str)) == []
    assert glom(['a'], nullable_list_of(str)) == ['a']
    with pytest.raises(GlomMatchError):
        glom([1], nullable_list_of(str))


def test_clamp():
    assert glom(range(10), [(M < 7) | Literal(7)]) == [0, 1, 2, 3, 4, 5, 6, 7, 7, 7]
    assert glom(range(10), [(M < 7) | Literal(SKIP)]) == [0, 1, 2, 3, 4, 5, 6]


def test_json_ref():
    assert glom(
        {'a': {'b': [0, 1]}},
        Ref('json',
            Match(Or(
                And(dict, {Ref('json'): Ref('json')}),
                And(list, [Ref('json')]),
                And(0, Auto(lambda t: None)),
                object)))) == {'a': {'b': [None, 1]}}


def test_nested_struct():
    """adapted from use case"""
    import json

    _json = lambda spec: Auto((json.loads, _str_json, Match(spec)))

    _str_json = Ref('json',
        Match(Or(
            And(dict, {Ref('json'): Ref('json')}),
            And(list, [Ref('json')]),
            And(type(u''), Auto(str)),
            object)))

    rule_spec = Match({
        'rule_id': Or('', Regex(r'\d+')),
        'rule_name': str,
        'effect': Or('approve', 'custom_approvers'),
        'rule_approvers': _json([{'pk': int, 'level': int}]),
        'rule_data': _json([  # list of condition-objects
            {
                Optional('value', 'null'): _json(
                    Or(None, int, float, str, [int, float, str])),
                'field': Auto(int),  # id of row from FilterField
                'operator': str,  # corresponds to FilterOperator.display_name
            }]),
        Optional('save_as_new', False): Or(str, bool),
    })

    rule = dict(
        rule_id='1',
        rule_name='test rule',
        effect='approve',
        rule_approvers=json.dumps([{'pk': 2, 'level': 1}]),
        rule_data=json.dumps([
            {'value': json.dumps([1, 2]), 'field': 2, 'operator': '>'},
            {'field': 2, 'operator': '=='}])
    )

    glom(rule, rule_spec)
    rule['save_as_new'] = 'true'
    glom(rule, rule_spec)
