
import pytest

from glom import glom, Path, T, S, Literal, Let, A, Vars, GlomError

from glom.core import ROOT
from glom.mutation import PathAssignError

def test_let():
    data = {'a': 1, 'b': [{'c': 2}, {'c': 3}]}
    output = [{'a': 1, 'c': 2}, {'a': 1, 'c': 3}]
    assert glom(data, (Let(a='a'), ('b', [{'a': S['a'], 'c': 'c'}]))) == output
    assert glom(data, ('b', [{'a': S[ROOT][Literal(T)]['a'], 'c': 'c'}])) == output

    with pytest.raises(TypeError):
        Let('posarg')
    with pytest.raises(TypeError):
        Let()

    assert glom([[1]], (Let(v=Vars()), [[A.v.a]], S.v.a)) == 1
    assert glom(1, (Let(v=lambda t: {}), A.v['a'], S.v['a'])) == 1
    with pytest.raises(GlomError):
        glom(1, (Let(v=lambda t: 1), A.v.a))

    class FailAssign(object):
        def __setattr__(self, name, val):
            raise Exception('nope')

    with pytest.raises(PathAssignError):
        glom(1, (Let(v=lambda t: FailAssign()), Path(A.v, 'a')))

    assert repr(Let(a=T.a.b)) == 'Let(a=T.a.b)'


def test_globals():
    assert glom([[1]], ([[A.globals.a]], S.globals.a)) == 1


def test_vars():
    let = Let(v=Vars({'b': 2}, c=3))
    assert glom(1, (let, A.v.a, S.v.a)) == 1
    with pytest.raises(AttributeError):
        glom(1, (let, S.v.a))  # check that Vars() inside a spec doesn't hold state
    assert glom(1, (let, Path(A, 'v', 'a'), S.v.a)) == 1
    assert glom(1, (let, S.v.b)) == 2
    assert glom(1, (let, S.v.c)) == 3
    assert repr(let) == "Let(v=Vars({'b': 2}, c=3))"
    assert repr(Vars(a=1, b=2)) in (
        "Vars(a=1, b=2)", "Vars(b=2, a=1)")
    assert repr(Vars(a=1, b=2).glomit(None, None)) in (
        "Vars({'a': 1, 'b': 2})", "Vars({'b': 2, 'a': 1})")

    assert repr(A.b["c"]) == "A.b['c']"
