
from glom import glom, OMIT, Path, Inspect, Coalesce, CoalesceError


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
