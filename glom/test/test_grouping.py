from glom.grouping import Group, First, Avg, Sum, Max, Min, Count, Limit
from glom import glom, T


def test_bucketing():
    assert glom(range(4), Group({lambda t: t % 2 == 0: [T]})) == {True: [0, 2], False: [1, 3]}
    assert (glom(range(6), Group({lambda t: t % 3: {lambda t: t % 2: [lambda t: t / 10.0]}})) ==
        {0: {0: [0.0], 1: [0.3]}, 1: {1: [0.1], 0: [0.4]}, 2: {0: [0.2], 1: [0.5]}})


def test_agg():
    t = list(range(10))
    assert glom(t, Group(First())) == 0
    assert glom(t, Group(T)) == 9  # this is basically Last

    assert glom(t, Group(Avg())) == 1.0 * sum(t) / len(t)
    assert glom(t, Group(Sum())) == sum(t)

    assert glom([0, 1, 0], Group(Max())) == 1
    assert glom([1, 0, 1], Group(Min())) == 0

    assert glom(range(10), Group({lambda t: t % 2: Count()})) == {
		0: 5, 1: 5}

    # assert glom(t, Group(Limit(1, T))) == 0
