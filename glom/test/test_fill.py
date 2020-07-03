from glom import Auto, Fill, T, S, glom, Format, Let

def test():
    assert glom('abc', Fill((T[0], {T[1]: T[2]}))) == ('a', {'b': 'c'})
    assert glom('123', Fill({T[0], frozenset([T[1], T[2]])})) == {'1', frozenset(['2', '3'])}
    assert glom('xyz', Fill([T[0], T[1], T[2]]))
    assert glom('abc', Fill(lambda t: t.upper())) == 'ABC'
    assert glom('a', Fill(1)) == 1
    assert Fill((T, T, T)).fill(1) == (1, 1, 1)

    target = {'data': [0, 2, 4]}
    assert glom(target, Fill((T['data'][-1], Auto('data.-2')))) == (4, 2)

    assert repr(Auto()) == 'Auto()'
    assert repr(Auto(T)) == 'Auto(T)'

    assert repr(Fill()) == 'Fill()'
    assert repr(Fill(T)) == 'Fill(T)'

    assert repr(Fill(len)) == 'Fill(len)'


def test_format():
    assert glom(dict(a=1, b=2), Format("{a}{b}")) == "12"
    assert glom(dict(a=1, b=2), (Let(a='a', b='b'), Format("{a}{b}", S))) == "12"
    assert repr(Format('')) == "Format('')"
    assert repr(Format('', S)) == "Format('', S)"
