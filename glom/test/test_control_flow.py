from pytest import raises

from glom import glom, Switch, GlomError


def test_switch():
    data = {'a': 1, 'b': 2}
    cases = [('c', lambda t: 3), ('a', 'a')]
    cases2 = dict(cases)
    assert glom(data, Switch(cases)) == 1
    assert glom(data, Switch(cases2)) == 1
    assert glom({'c': None}, Switch(cases)) == 3
    assert glom({'c': None}, Switch(cases2)) == 3
    assert glom(None, Switch(cases, default=4)) == 4
    assert glom(None, Switch({}, default=4)) == 4
    with raises(GlomError):
    	glom(None, Switch(cases))
    with raises(ValueError):
    	Switch({})
    with raises(TypeError):
    	Switch("wrong type")
    repr(Switch(cases))
