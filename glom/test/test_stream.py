from itertools import count

from ..stream import Iter
from ..core import glom


def test_iter():
	assert list(glom("123", Iter(int))) == [1, 2, 3]
	cnt = count()
	cnt_1 = glom(cnt, Iter(lambda t: t + 1))
	assert (cnt_1.next(), cnt_1.next()) == (1, 2)
	assert cnt.next() == 2
