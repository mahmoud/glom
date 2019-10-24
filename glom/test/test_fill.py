from glom import Fill, T, glom

def test():
    assert glom('abc', Fill((T[0], {T[1]: T[2]}))) == ('a', {'b': 'c'})
    assert glom('123', Fill({T[0], frozenset([T[1], T[2]])})) == {'1', frozenset(['2', '3'])}
    assert glom('xyz', Fill([T[0], T[1], T[2]]))
    assert glom('abc', Fill(lambda t: t.upper())) == 'ABC'
    assert glom('a', Fill(1)) == 1
    assert Fill((T, T, T)).fill(1) == (1, 1, 1)
