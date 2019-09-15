
import pytest

from itertools import count, dropwhile, chain

from ..stream import Iter, Partial
from ..core import glom, SKIP, STOP, T, Call, Spec


RANGE_5 = list(range(5))


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


# @pytest.mark.skip(reason='filter broken until _handle_tuple and SKIP interaction fixed')
def test_filter():
    is_odd = lambda x: x % 2
    spec = Iter().filter(is_odd)
    out = glom(RANGE_5, spec)
    assert list(out) == [1, 3]

    # let's just make sure we're actually streaming just in case
    counter = count()
    out = glom(counter, spec)
    assert next(out) == 1
    assert next(out) == 3
    assert next(counter) == 4
    assert next(counter) == 5
    assert next(out) == 7


def test_map():
    spec = Iter().map(lambda x: x * 2)
    out = glom(RANGE_5, spec)
    assert list(out) == [0, 2, 4, 6, 8]


def test_split_chain():
    falsey_stream = [1, None, None, 2, 3, None, 4]
    spec = Iter().split()
    out = glom(falsey_stream, spec)
    assert list(out) == [[1], [2, 3], [4]]

    spec = Iter().split().chain()
    out = glom(falsey_stream, spec)
    assert list(out) == [1, 2, 3, 4]


def test_chunked():
    int_list = list(range(9))

    spec = Iter().chunked(3)
    out = glom(int_list, spec)
    assert list(out) == [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

    spec = Iter().chunked(3).map(sum)
    out = glom(int_list, spec)
    assert list(out) == [3, 12, 21]


def test_windowed():
    int_list = list(range(5))

    spec = Iter().windowed(3)
    out = glom(int_list, spec)
    assert list(out) == [(0, 1, 2), (1, 2, 3), (2, 3, 4)]

    spec = spec.filter(lambda x: bool(x[0] % 2)).map(sum)
    out = glom(int_list, spec)
    assert next(out) == 6

    out = glom(range(10), spec)
    assert list(out) == [6, 12, 18, 24]


def test_unique():
    int_list = list(range(10))

    spec = Iter().unique()
    out = glom(int_list, spec)
    assert list(out) == int_list

    spec = Iter(lambda x: x % 4).unique()
    out = glom(int_list, spec)
    assert list(out) == int_list[:4]


def test_slice():
    cnt = count()

    spec = Iter().slice(3)
    out = glom(cnt, spec)

    assert list(out) == [0, 1, 2]
    assert next(cnt) == 3

    out = glom(range(10), Iter().slice(1, 5))
    assert list(out) == [1, 2, 3, 4]

    out = glom(range(10), Iter().slice(1, 6, 2))
    assert list(out) == [1, 3, 5]

    out = glom(range(10), Iter().limit(3))
    assert list(out) == [0, 1, 2]

    out = glom(range(5), Iter().limit(10))
    assert list(out) == [0, 1, 2, 3, 4]


def test_zip():
    out = glom(range(3), Iter().zip())
    assert list(out) == [(0, 0), (1, 1), (2, 2)]

    out = glom(range(3), Iter().zip().chain())
    assert list(out) == [0, 0, 1, 1, 2, 2]

    out = glom(range(5), Iter().zip().map(lambda x: (x[0], x[1].bit_length())))
    assert list(out) == [(0, 0), (1, 1), (2, 2), (3, 2), (4, 3)]

    target = [1, 2, 3]
    spec = Iter().zip(otherspec=Spec(reversed))
    out = glom(target, spec)
    assert list(out) == [(1, 3), (2, 2), (3, 1)]
