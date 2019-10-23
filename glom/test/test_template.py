from glom import Template, T, glom

def test():
    assert glom('abc', Template((T[0], {T[1]: T[2]}))) == ('a', {'b': 'c'})
    assert glom('123', Template({T[0], frozenset([T[1], T[2]])})) == {'1', frozenset(['2', '3'])}
    assert glom('xyz', Template([T[0], T[1], T[2]]))
    assert glom('abc', Template(lambda t: t.upper())) == 'ABC'
    assert glom('a', 1) == 1
