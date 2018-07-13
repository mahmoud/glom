import pytest

from glom import glom, Path, T
from glom.mutable import Assign


def test_assign():
    assert glom({}, Assign(T['a'], 1)) == {'a': 1}

