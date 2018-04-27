
from glom import glom, Path, Inspect, Coalesce


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
