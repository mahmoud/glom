from __future__ import division

from glom.grouping import Group, First, Avg, Sum, Max, Min, Count, Sample, Limit
from glom import glom, T

from glom.reduction import Merge, Flatten


def test_bucketing():
    assert glom(range(4), Group({lambda t: t % 2 == 0: [T]})) == {True: [0, 2], False: [1, 3]}
    assert (glom(range(6), Group({lambda t: t % 3: {lambda t: t % 2: [lambda t: t / 10.0]}})) ==
        {0: {0: [0.0], 1: [0.3]}, 1: {1: [0.1], 0: [0.4]}, 2: {0: [0.2], 1: [0.5]}})


def test_agg():
    t = list(range(10))
    assert glom(t, Group(First())) == 0
    assert glom(t, Group(T)) == 9  # this is basically Last

    assert glom(t, Group(Avg())) == sum(t) / len(t)
    assert glom(t, Group(Sum())) == sum(t)

    assert glom([0, 1, 0], Group(Max())) == 1
    assert glom([1, 0, 1], Group(Min())) == 0

    assert glom(range(10), Group({lambda t: t % 2: Count()})) == {
		0: 5, 1: 5}


def test_limit():
    t = list(range(10))
    assert glom(t, Group(Limit(1, T))) == 0
    assert glom(t, Group(Limit(3, Max()))) == 2
    assert glom(t, Group(Limit(3, [T]))) == [0, 1, 2]


def test_reduce():
    assert glom([[1], [2, 3]], Group(Flatten())) == [1, 2, 3]
    assert glom([{'a': 1}, {'b': 2}], Group(Merge())) == {'a': 1, 'b': 2}
    assert glom([[[1]], [[2, 3], [4]]], Group(Flatten(Flatten()))) == [1, 2, 3, 4]


def test_sample():
    assert glom([1, 2, 3], Group(Sample(5))) == [1, 2, 3]
    s = glom([1, 2, 3], Group(Sample(2)))
    assert s in [[1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2]]