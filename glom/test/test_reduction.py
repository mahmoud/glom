
import pytest

from glom import glom, T, Sum, Fold, Flatten, Coalesce, flatten, FoldError


def test_sum_integers():
    target = list(range(5))

    assert glom(target, Sum()) == 10

    assert glom(target, Sum(init=lambda: 2)) == 12

    target = []
    assert glom(target, Sum()) == 0


    target = [{"num": 3}, {"num": 2}, {"num": -1}]
    assert glom(target, Sum(['num'])) == 4

    target = target + [{}]  # add a non-compliant dict
    assert glom(target, Sum([Coalesce('num', default=0)])) ==4

    repr(Sum())


def test_sum_seqs():
    target = [(x,) for x in range(4)]
    assert glom(target, Sum(init=tuple)) == (0, 1, 2, 3)

    # would not work with builtin sum(), gets:
    # "TypeError: sum() can't sum strings [use ''.join(seq) instead]"
    # Works here for now. If we're ok with that error, then we can
    # switch to sum().
    target = ['a', 'b', 'cd']
    assert glom(target, Sum(init=str)) == 'abcd'

    target = [['a'], ['b'], ['cde'], ['']]

    assert glom(target, Sum(Sum(init=list), init=str)) == 'abcde'


def test_fold():
    target = range(1, 5)
    assert glom(target, Fold(T, int)) == 10
    assert glom(target, Fold(T, init=lambda: 2)) == 12

    assert glom(target, Fold(T, lambda: 1, op=lambda l, r: l * r)) == 24

    repr(Fold(T, int))


def test_flatten():
    target = [[1], [2], [3, 4]]
    assert glom(target, Flatten()) == [1, 2, 3, 4]

    target = [(1, 2), [3]]
    assert glom(target, Flatten()) == [1, 2, 3]

    gen = glom(target, Flatten(init='lazy'))
    assert next(gen) == 1
    assert list(gen) == [2, 3]

    repr(Flatten())


def test_flatten_func():
    target = [[1], [2], [3, 4]]
    assert flatten(target) == [1, 2, 3, 4]

    two_level_target = [[x] for x in target]
    assert flatten(two_level_target, levels=2) == [1, 2, 3, 4]

    unflattenable = 2

    with pytest.raises(FoldError):
        assert flatten(unflattenable)

    # kind of an odd use
    assert flatten(['a', 'b', 'cd'], init=str) == 'abcd'

    # another odd case
    subspec_target = {'items': {'numbers': [1, 2, 3]}}
    assert (flatten(subspec_target, spec='items.numbers', init=int) == 6)
