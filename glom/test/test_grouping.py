from glom.grouping import Group
from glom import glom, T


def test_bucketing():
    assert glom([1, 2, 3, 4], Group({lambda t: t % 2 == 0: [T]})) == {True: [2, 4], False: [1, 3]}

