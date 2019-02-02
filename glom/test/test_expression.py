import glom
from glom.expression import F


def test():
    F('a') > 3
    (F('a') > 3) & (F('b') < 10)
    vals = [
        {'a': i, 'b': (i * 2) % 100, 'c': (i * 3) % 100} for i in range(100)]
    results = glom.glom(
        vals, [glom.Check(
            (F('a') > glom.Literal(3)) & (F('b') < glom.Literal(10)) | (F('c') == glom.Literal(3)),
            default=glom.SKIP)])
    for r in results:
        assert r['a'] > 3 and r['b'] < 10 or r['c'] == 3
