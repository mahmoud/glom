from glom import Name, Globals, glom, T, ROOT, S, Literal


def test_var():
    data = {'a': 1, 'b': [{'c': 2}, {'c': 3}]}
    output = [{'a': 1, 'c': 2}, {'a': 1, 'c': 3}]
    glom(data, (Name(a=T['a']), 'b', [{'a': S['a'], 'c': 'c'}])) == output
    assert glom(data, (Globals(a=T['a']), 'b', [{'a': S['a'], 'c': 'c'}])) == output
    glom(data, ('b', [{'a': S[ROOT][Literal(T)]['a'], 'c': 'c'}])) == output