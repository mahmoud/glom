from glom.grouping import Group
from glom import glom, T


def test_bucketing():
    assert glom(range(4), Group({lambda t: t % 2 == 0: [T]})) == {True: [0, 2], False: [1, 3]}
    assert (glom(range(6), Group({lambda t: t % 3: {lambda t: t % 2: [lambda t: t / 10.0]}})) ==
        {0: {0: [0.0], 1: [0.3]}, 1: {1: [0.1], 0: [0.4]}, 2: {0: [0.2], 1: [0.5]}})
