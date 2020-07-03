from glom import glom, Switch


def test_switch():
    data = {'a': 1, 'b': 2}
    cases = [('c', lambda t: 3), ('a', 'a')]
    cases2 = dict(cases)
    assert glom(data, Switch(cases)) == 1
    assert glom(data, Switch(cases2)) == 1
    repr(Switch(cases))
