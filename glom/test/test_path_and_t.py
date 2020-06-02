
from pytest import raises

from glom import glom, Path, S, T, PathAccessError, GlomError

def test_list_path_access():
    assert glom(list(range(10)), Path(1)) == 1


def test_path():
    _obj = object()
    target = {'a': {'b.b': [None, {_obj: [None, None, 'd']}]}}

    assert glom(target, Path('a', 'b.b', 1, _obj, -1)) == 'd'


def test_empty_path_access():
    target = {}

    assert glom(target, Path()) is target
    assert glom(target, (Path(), Path(), Path())) is target

    dup_dict = glom(target, {'target': Path(),
                             'target2': Path()})
    dup_dict['target'] is target
    dup_dict['target2'] is target


def test_path_t_roundtrip():
    # check that T repr roundrips
    assert repr(T['a'].b.c()) == "T['a'].b.c()"

    # check that Path repr roundtrips
    assert repr(Path('a', 1, 'b.b', -1.0)) == "Path('a', 1, 'b.b', -1.0)"

    # check that Path repr roundtrips when it contains Ts
    assert repr(Path(T['a'].b, 'c', T['d'].e)) == "Path(T['a'].b, 'c', T['d'].e)"

    # check that T instances containing Path access revert to repring with Path
    assert repr(Path(T['a'].b, 'c', T['d'].e).path_t) == "Path(T['a'].b, 'c', T['d'].e)"

    # check that Paths containing only T objects reduce to a T (joining the T objects)
    assert repr(Path(T['a'].b, T.c())) == "T['a'].b.c()"

    # check that multiple nested paths reduce
    assert repr(Path(Path(Path('a')))) == "Path('a')"

    # check builtin repr
    assert repr(T[len]) == 'T[len]'
    assert repr(T.func(len, sum)) == 'T.func(len, sum)'


def test_path_access_error_message():

    # test fuzzy access
    with raises(GlomError) as exc_info:
        glom({}, 'a.b')
    assert ("PathAccessError: could not access 'a', part 0 of Path('a', 'b'), got error: KeyError"
            in exc_info.exconly())
    ke = repr(KeyError('a'))  # py3.7+ changed the keyerror repr
    assert repr(exc_info.value) == "PathAccessError(" + ke + ", Path('a', 'b'), 0)"

    # test multi-part Path with T, catchable as a KeyError
    with raises(KeyError) as exc_info:
        # don't actually use glom to copy your data structures please
        glom({'a': {'b': 'c'}}, Path('a', T.copy(), 'd'))
    assert ("PathAccessError: could not access 'd', part 3 of Path('a', T.copy(), 'd'), got error: KeyError"
            in exc_info.exconly())
    ke = repr(KeyError('d'))  # py3.7+ changed the keyerror repr
    assert repr(exc_info.value) == "PathAccessError(" + ke + ", Path('a', T.copy(), 'd'), 3)"

    # test AttributeError
    with raises(GlomError) as exc_info:
        glom({'a': {'b': 'c'}}, Path('a', T.b))
    assert ("PathAccessError: could not access 'b', part 1 of Path('a', T.b), got error: AttributeError"
            in exc_info.exconly())
    ae = repr(AttributeError("'dict' object has no attribute 'b'"))
    assert repr(exc_info.value) == "PathAccessError(" + ae + ", Path(\'a\', T.b), 1)"


def test_t_picklability():
    import pickle

    class TargetType(object):
        def __init__(self):
            self.attribute = lambda: None
            self.attribute.method = lambda: {'key': lambda x: x * 2}

    spec = T.attribute.method()['key'](x=5)

    rt_spec = pickle.loads(pickle.dumps(spec))
    assert repr(spec) == repr(rt_spec)

    assert glom(TargetType(), spec) == 10

    s_spec = S.attribute
    assert repr(s_spec) == repr(pickle.loads(pickle.dumps(s_spec)))


def test_path_len():

    assert len(Path()) == 0
    assert len(Path('a', 'b', 'c')) == 3
    assert len(Path.from_text('1.2.3.4')) == 4

    assert len(Path(T)) == 0
    assert len(Path(T.a.b.c)) == 3
    assert len(Path(T.a()['b'].c.d)) == 5


def test_path_getitem():
    path = Path(T.a.b.c)

    assert path[0] == Path(T.a)
    assert path[1] == Path(T.b)
    assert path[2] == Path(T.c)
    assert path[-1] == Path(T.c)
    assert path[-2] == Path(T.b)

    with raises(IndexError, match='Path index out of range'):
        path[4]

    with raises(IndexError, match='Path index out of range'):
        path[-14]
    return


def test_path_slices():
    path = Path(T.a.b, 1, 2, T(test='yes'))

    assert path[::] == path

    # positive indices
    assert path[3:] == Path(2, T(test='yes'))
    assert path[1:3] == Path(T.b, 1)
    assert path[:3] == Path(T.a.b, 1)

    # positive indices backwards
    assert path[2:1] == Path()

    # negative indices forward
    assert path[-1:] == Path(T(test='yes'))
    assert path[:-2] == Path(T.a.b, 1)
    assert path[-3:-1] == Path(1, 2)

    # negative indices backwards
    assert path[-1:-3] == Path()

    # slicing and stepping
    assert path[1::2] == Path(T.b, 2)


def test_path_values():
    path = Path(T.a.b, 1, 2, T(test='yes'))

    assert path.values() == ('a', 'b', 1, 2, ((), {'test': 'yes'}))

    assert Path().values() == ()


def test_path_items():
    path = Path(T.a, 1, 2, T(test='yes'))

    assert path.items() == (('.', 'a'),
                            ('P', 1), ('P', 2),
                            ('(', ((), {'test': 'yes'})))

    assert Path().items() == ()


def test_path_eq():
    assert Path('a', 'b') == Path('a', 'b')
    assert Path('a') != Path('b')

    assert Path() != object()


def test_path_eq_t():
    assert Path(T.a.b) == T.a.b
    assert Path(T.a.b.c) != T.a.b



def test_path_null():
    assert repr(Path.from_text('a?.b')) == "Path('a?', 'b')"
    val = {'a': {'b': None}}
    # null check on non-null has no effect
    assert glom(val, 'a?.b') == glom(val, 'a.b')
    # null check on null returns None instead of error
    with raises(PathAccessError):
        glom(val, 'a.b.c')
    assert glom(val, 'a.b?.c') is None
    # check that '?' in wrong place raises error
    with raises(ValueError):
        glom(val, 'a.b??')
    # check that '?' on non-null-segment still raises error on null segment
    with raises(PathAccessError):
        glom(val, 'a?.b.c')


def test_startswith():
    ref = T.a.b[1]

    assert Path(ref).startswith(T)
    assert Path(ref).startswith(T.a.b)
    assert Path(ref).startswith(ref)
    assert Path(ref).startswith(ref.c) is False

    assert Path('a.b.c').startswith(Path())
    assert Path('a.b.c').startswith('a.b.c')

    with raises(TypeError):
        assert Path('a.b.c').startswith(None)

    return


def test_from_t_identity():
    ref = Path(T.a.b)
    assert ref.from_t() == ref
    assert ref.from_t() is ref


def test_t_dict_key():
    target = {'a': 'A'}
    assert glom(target, {T['a']: 'a'}) == {'A': 'A'}
