
from glom import glom, Sum

def test_sum_basic():

    assert glom(list(range(5)), Sum()) == 10
