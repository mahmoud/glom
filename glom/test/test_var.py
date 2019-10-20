from glom import glom, T, ROOT, S, Literal, Let


def test_var():
    data = {'a': 1, 'b': [{'c': 2}, {'c': 3}]}
    output = [{'a': 1, 'c': 2}, {'a': 1, 'c': 3}]
    assert glom(data, Let(a='a').over(('b', [{'a': S['a'], 'c': 'c'}]))) == output
    assert glom(data, ('b', [{'a': S[ROOT][Literal(T)]['a'], 'c': 'c'}])) == output
