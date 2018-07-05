
import pytest

from glom import glom, OMIT, Path, Inspect, Coalesce, CoalesceError, Literal, Call, T, S
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


def test_list_item_lift_and_access():
    val = {'d': {'e': ['f']}}

    assert glom(val, ('d.e', lambda x: x[0])) == 'f'
    assert glom(val, ('d.e', [(lambda x: {'f': x[0]}, 'f')])) == ['f']


def test_coalesce():
    val = {'a': {'b': 'c'},  # basic dictionary nesting
           'd': {'e': ['f'],    # list in dictionary
                 'g': 'h'},
           'i': [{'j': 'k', 'l': 'm'}],  # list of dictionaries
           'n': 'o'}

    assert glom(val, 'a.b') == 'c'
    assert glom(val, Coalesce('xxx', 'yyy', 'a.b')) == 'c'

    with pytest.raises(CoalesceError) as exc_info:
        glom(val, Coalesce('xxx', 'yyy'))

    msg = exc_info.exconly()
    assert "'xxx'" in msg
    assert "'yyy'" in msg
    assert msg.count('PathAccessError') == 2
    assert "[PathAccessError(KeyError('xxx',), Path('xxx'), 0), PathAccessError(KeyError('yyy',), Path('yyy'), 0)], [])" in repr(exc_info.value)

    # check that defaulting works
    assert glom(val, Coalesce('xxx', 'yyy', default='zzz')) == 'zzz'

    # check that default_factory works
    sentinel_list = []
    factory = lambda: sentinel_list
    assert glom(val, Coalesce('xxx', 'yyy', default_factory=factory)) is sentinel_list

    with pytest.raises(ValueError):
        Coalesce('x', 'y', default=1, default_factory=list)

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


def test_abstract_iterable():
    assert isinstance([], glom_core._AbstractIterable)

    class MyIterable(object):
        def __iter__(self):
            return iter([1, 2, 3])

    assert isinstance(MyIterable(), glom_core._AbstractIterable)


def test_call_and_target():
    class F(object):
        def __init__(s, a, b, c): s.a, s.b, s.c = a, b, c

    call_f = Call(F, kwargs=dict(a=T, b=T, c=T))
    assert repr(call_f)
    val = glom(1, call_f)
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
    assert repr(Spec('a.b.c')) == "Spec('a.b.c')"

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




def test_scope():
    assert glom(None, S['foo'], scope={'foo': 'bar'}) == 'bar'

    target = range(3)
    spec = [(S, lambda S: S['multiplier'] * S[T])]
    scope = {'multiplier': 2}
    assert glom(target, spec, scope=scope) == [0, 2, 4]
    scope = {'multiplier': 2.5}
    assert glom(target, spec, scope=scope) == [0.0, 2.5, 5.0]


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

    with pytest.raises(glom_core.GlomError):
        spec = T['system']['comets'][-1].values()
        output = glom(target, spec)


def test_glom_extra_kwargs():
    # for coverage
    with pytest.raises(TypeError):
        glom({'a': 'a'}, 'a', invalid_kwarg='yes')


def test_inspect():
    # test repr
    assert repr(Inspect()) == '<INSPECT>'

    target = {'a': {'b': 'c'}}

    import pdb
    # test breakpoint
    assert Inspect(breakpoint=True).breakpoint == pdb.set_trace
    with pytest.raises(TypeError):
        Inspect(breakpoint='lol')

    tracker = []
    spec = {'a': Inspect('a.b', echo=False, breakpoint=lambda: tracker.append(True))}

    glom(target, spec)

    assert len(tracker) == 1

    # test post_mortem
    assert Inspect(post_mortem=True).post_mortem == pdb.post_mortem
    with pytest.raises(TypeError):
        Inspect(post_mortem='lol')

    tracker = []
    spec = {'a': Inspect('nope.nope', post_mortem=lambda: tracker.append(True))}

    assert glom(target, spec, default='default') == 'default'
    assert len(tracker) == 1
