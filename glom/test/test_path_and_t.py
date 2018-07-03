
from pytest import raises

from glom import glom, Path, T, PathAccessError, GlomError

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


def test_path_access_error_message():

    # test fuzzy access
    with raises(GlomError) as exc_info:
        glom({}, 'a.b')
    assert ("PathAccessError: could not access 'a', part 0 of Path('a', 'b'), got error: KeyError"
            in exc_info.exconly())
    assert repr(exc_info.value) == "PathAccessError(KeyError('a',), Path('a', 'b'), 0)"

    # test multi-part Path with T, catchable as a KeyError
    with raises(KeyError) as exc_info:
        # don't actually use glom to copy your data structures please
        glom({'a': {'b': 'c'}}, Path('a', T.copy(), 'd'))
    assert ("PathAccessError: could not access 'd', part 3 of Path('a', T.copy(), 'd'), got error: KeyError"
            in exc_info.exconly())
    assert repr(exc_info.value) == "PathAccessError(KeyError('d',), Path('a', T.copy(), 'd'), 3)"

    # test AttributeError
    with raises(GlomError) as exc_info:
        glom({'a': {'b': 'c'}}, Path('a', T.b))
    assert ("PathAccessError: could not access 'b', part 1 of Path('a', T.b), got error: AttributeError"
            in exc_info.exconly())
    assert repr(exc_info.value) == """PathAccessError(AttributeError("\'dict\' object has no attribute \'b\'",), Path(\'a\', T.b), 1)"""
