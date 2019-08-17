from ..stream import Iter
from ..core import glom


def test_iter():
	assert glom("123", Iter(int)) == [1, 2, 3]
