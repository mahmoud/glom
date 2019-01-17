
from glom import glom, T, Sum, Fold, Coalesce

def test_sum_integers():
    target = list(range(5))

    assert glom(target, Sum()) == 10

    assert glom(target, Sum(start=2)) == 12

    target = []
    assert glom(target, Sum()) == 0


    target = [{"num": 3}, {"num": 2}, {"num": -1}]
    assert glom(target, Sum(['num'])) == 4

    target = target + [{}]  # add a non-compliant dict
    assert glom(target, Sum([Coalesce('num', default=0)])) ==4


def test_sum_seqs():
    target = [(x,) for x in range(4)]
    assert glom(target, Sum(start=())) == (0, 1, 2, 3)

    # would not work with builtin sum(), gets:
    # "TypeError: sum() can't sum strings [use ''.join(seq) instead]"
    # Works here for now. If we're ok with that error, then we can
    # switch to sum().
    target = ['a', 'b', 'cd']
    assert glom(target, Sum(start='')) == 'abcd'

    target = [['a'], ['b'], ['cde'], ['']]

    assert glom(target, Sum(Sum(start=[]), start='')) == 'abcde'


def test_fold():
    target = range(1, 5)
    assert glom(target, Fold(T, 0)) == 10
    assert glom(target, Fold(T, start=2)) == 12

    assert glom(target, Fold(T, 1, op=lambda l, r: l * r)) == 24
