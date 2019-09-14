
import pytest

from itertools import count, dropwhile, chain

from ..stream import Iter, Partial
from ..core import glom, SKIP, STOP, T


def test_iter():
    assert list(glom(['1', '2', '3'], Iter(int))) == [1, 2, 3]
    cnt = count()
    cnt_1 = glom(cnt, Iter(lambda t: t + 1))
    assert (next(cnt_1), next(cnt_1)) == (1, 2)
    assert next(cnt) == 2

    assert list(glom(['1', '2', '3'], (Iter(int), enumerate))) == [(0, 1), (1, 2), (2, 3)]

    assert list(glom([1, SKIP, 2], Iter())) == [1, 2]
    assert list(glom([1, STOP, 2], Iter())) == [1]

    with pytest.raises(TypeError):
        Iter(nonexistent_kwarg=True)

    assert list(glom(range(10), Partial(dropwhile)(lambda x: x < 5)(T))) == (
        [5, 6, 7, 8, 9])

    assert list(glom([1, 2], Partial(chain, T, T))) == [1, 2, 1, 2]
