import pytest

from glom import glom, Path, T
from glom.mutable import Assign, assign


def test_assign():
    class Foo(object): None
    assert glom({}, Assign(T['a'], 1)) == {'a': 1}
    assert glom({'a': {}}, Assign(T['a']['a'], 1)) == {'a': {'a': 1}}
    assert glom({'a': {}}, Assign('a.a', 1)) == {'a': {'a': 1}}
    assert glom(Foo(), Assign(T.a, 1)).a == 1
    assert glom({}, Assign('a', 1)) == {'a': 1}
    assert glom(Foo(), Assign('a', 1)).a == 1
    assert glom({'a': Foo()}, Assign('a.a', 1))['a'].a == 1
    def r():
        r = {}
        r['r'] = r
        return r
    assert glom(r(), Assign('r.r.r.r.r.r.r.r.r', 1)) == {'r': 1}
    assert glom(r(), Assign(T['r']['r']['r']['r'], 1)) == {'r': 1}
    assert glom(r(), Assign(Path('r', 'r', T['r']), 1)) == {'r': 1}
    assert assign(r(), Path('r', 'r', T['r']), 1) == {'r': 1}
    with pytest.raises(TypeError):
        glom({}, Assign(1, 'a'))
    with pytest.raises(ValueError):
        glom({}, Assign(T, 1))
