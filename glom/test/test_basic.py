
import pytest

from glom import glom, OMIT, Path, Inspect, Coalesce, CoalesceError, Literal, Call, T
import glom.core as glom_core
from glom.core import Spec, UP  # probationary


def test_initial_integration():
    class Example(object):
        pass

    example = Example()
    subexample = Example()
    subexample.name = 'good_name'
    example.mapping = {'key': subexample}

    val = {'a': {'b': 'c'},  # basic dictionary nesting
           'example': example,  # basic object
           'd': {'e': ['f'],    # list in dictionary
                 'g': 'h'},
           'i': [{'j': 'k', 'l': 'm'}],  # list of dictionaries
           'n': 'o'}

    spec = {'a': (Inspect(recursive=True), 'a', 'b'),  # inspect just prints here
            'name': 'example.mapping.key.name',  # test object access
            'e': 'd.e',  # d.e[0] or d.e: (callable to fetch 0)
            'i': ('i', [{'j': 'j'}]),  # TODO: support True for cases when the value should simply be mapped into the field name?
            'n': ('n', lambda n: n.upper()),
            'p': Coalesce('xxx',
                          'yyy',
                          default='zzz')}

    ret = glom(val, spec)

    print('in: ', val)
    print('got:', ret)
    expected = {'a': 'c',
                'name': 'good_name',
                'e': ['f'],
                'i': [{'j': 'k'}],
                'n': 'O',
                'p': 'zzz'}
    print('exp:', expected)

    assert ret == expected


def test_list_path_access():
    assert glom(list(range(10)), Path(1)) == 1


def test_list_item_lift_and_access():
    val = {'d': {'e': ['f']}}

    assert glom(val, ('d.e', lambda x: x[0])) == 'f'
    assert glom(val, ('d.e', [(lambda x: {'f': x[0]}, 'f')])) == ['f']


def test_empty_path_access():
    target = {}

    assert glom(target, Path()) is target
    assert glom(target, (Path(), Path(), Path())) is target

    dup_dict = glom(target, {'target': Path(),
                             'target2': Path()})
    dup_dict['target'] is target
    dup_dict['target2'] is target


def test_coalesce():
    val = {'a': {'b': 'c'},  # basic dictionary nesting
           'd': {'e': ['f'],    # list in dictionary
                 'g': 'h'},
           'i': [{'j': 'k', 'l': 'm'}],  # list of dictionaries
           'n': 'o'}

    assert glom(val, 'a.b') == 'c'
    assert glom(val, Coalesce('xxx', 'yyy', 'a.b')) == 'c'

    try:
        glom(val, Coalesce('xxx', 'yyy'))
    except CoalesceError as ce:
        msg = str(ce)
        assert "'xxx'" in msg
        assert "'yyy'" in msg
        assert msg.count('PathAccessError') == 2
    else:
        assert False, 'expected a CoalesceError'

    # check that defaulting works
    assert glom(val, Coalesce('xxx', 'yyy', default='zzz')) == 'zzz'

    # check that arbitrary values can be skipped
    assert glom(val, Coalesce('xxx', 'yyy', 'a.b', default='zzz', skip='c')) == 'zzz'

    # check that arbitrary exceptions can be ignored
    assert glom(val, Coalesce(lambda x: 1/0, 'a.b', skip_exc=ZeroDivisionError)) == 'c'


def test_omit():
    target = {'a': {'b': 'c'},  # basic dictionary nesting
           'd': {'e': ['f'],    # list in dictionary
                 'g': 'h'},
           'i': [{'j': 'k', 'l': 'm'}],  # list of dictionaries
           'n': 'o'}

    res = glom(target, {'a': 'a.b',
                        'z': Coalesce('x', 'y', default=OMIT)})
    assert res['a'] == 'c'  # sanity check

    assert 'x' not in target
    assert 'y' not in target
    assert 'z' not in res

    # test that it works on lists
    target = range(7)
    res = glom(target, [lambda t: t if t % 2 else OMIT])
    assert res == [1, 3, 5]


def test_top_level_default():
    expected = object()
    val = glom({}, 'a.b.c', default=expected)
    assert val is expected

    val = glom({}, lambda x: 1/0, skip_exc=ZeroDivisionError)
    assert val is None

    val = glom({}, lambda x: 1/0, skip_exc=ZeroDivisionError, default=expected)
    assert val is expected

    with pytest.raises(KeyError):
        # p degenerate case if you ask me
        glom({}, 'x', skip_exc=KeyError, default=glom_core._MISSING)

    return


def test_literal():
    expected = {'value': 'c',
                'type': 'a.b'}
    target = {'a': {'b': 'c'}}
    val = glom(target, {'value': 'a.b',
                        'type': Literal('a.b')})

    assert val == expected

    assert glom(None, Literal('success')) == 'success'
    assert repr(Literal(3.14)) == 'Literal(3.14)'


def test_path():
    _obj = object()
    target = {'a': {'b.b': [None, {_obj: [None, None, 'd']}]}}

    assert glom(target, Path('a', 'b.b', 1, _obj, -1)) == 'd'


def test_abstract_iterable():
    assert isinstance([], glom_core._AbstractIterable)

    class MyIterable(object):
        def __iter__(self):
            return iter([1, 2, 3])

    assert isinstance(MyIterable(), glom_core._AbstractIterable)


def test_call_and_target():
    class F(object):
        def __init__(s, a, b, c): s.a, s.b, s.c = a, b, c
    val = glom(1, Call(F, kwargs=dict(a=T, b=T, c=T)))
    assert (val.a, val.b, val.c) == (1, 1, 1)
    class F(object):
        def __init__(s, a): s.a = a
    val = glom({'one': F('two')}, Call(F, args=(T['one'].a,)))
    assert val.a == 'two'
    assert glom({'a': 1}, Call(F, kwargs=T)).a == 1
    assert glom([1], Call(F, args=T)).a == 1
    assert glom(F, T(T)).a == F
    assert glom([F, 1], T[0](T[1]).a) == 1
    assert glom([[1]], T[0][0][0][UP]) == 1


def test_spec_and_recursion():
    # Call doesn't normally recurse, but Spec can make it do so
    assert glom(
        ['a', 'b', 'c'],
        Call(list, args=(
            Spec(Call(reversed, args=(Spec(T),))),)
        )) == ['c', 'b', 'a']
    assert glom(['cat', {'cat': 1}], T[1][T[0]]) == 1
    assert glom(
        [['ab', 'cd', 'ef'], ''.join],
        Call(T[1], args=(Spec((T[0], [T[1:]])),))) == 'bdf'


def test_seq_getitem():
    assert glom({'items': [0, 1, 2, 3]}, 'items.1') == 1
    assert glom({'items': (9, 8, 7, 6)}, 'items.-3') == 8

    with pytest.raises(glom_core.PathAccessError):
        assert glom({'items': (9, 8, 7, 6)}, 'items.fun')


# examples from http://sedimental.org/glom_restructured_data.html

def test_beyond_access():
    # 1
    target = {'galaxy': {'system': {'planet': 'jupiter'}}}
    spec = 'galaxy.system.planet'

    output = glom(target, spec)
    assert output == 'jupiter'

    # 2
    target = {'system': {'planets': [{'name': 'earth'}, {'name': 'jupiter'}]}}

    output = glom(target, ('system.planets', ['name']))
    assert output == ['earth', 'jupiter']

    # 3
    target = {'system': {'planets': [{'name': 'earth', 'moons': 1},
                                     {'name': 'jupiter', 'moons': 69}]}}
    spec = {'names': ('system.planets', ['name']),
            'moons': ('system.planets', ['moons'])}

    output = glom(target, spec)
    assert output == {'names': ['earth', 'jupiter'], 'moons': [1, 69]}


def test_python_native():
    # 4
    target = {'system': {'planets': [{'name': 'earth', 'moons': 1},
                                     {'name': 'jupiter', 'moons': 69}]}}


    output = glom(target, {'moon_count': ('system.planets', ['moons'], sum)})
    assert output == {'moon_count': 70}

    # 5
    spec = T['system']['planets'][-1].values()

    output = glom(target, spec)
    assert set(output) == set(['jupiter', 69])  # for ordering reasons

    # with pytest.raises(glom_core.PathAccessError):  # TODO
    #     spec = T['system']['comets'][-1].values()
    #     output = glom(target, spec)
