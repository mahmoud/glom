import pytest

from glom import glom
from glom.matching import Match, M


def test():
    glom(1, Match(1))
    glom(1, Match(int))
    glom([1], Match([int]))
    glom({"a": 1, "b": 2}, Match({str: int}))
    glom(2, M == 2)
    glom(int, M == int)
    glom(1.0, M > 0)

