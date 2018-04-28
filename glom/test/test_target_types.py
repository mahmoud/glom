
from __future__ import print_function

import pytest

import glom
from glom import Glommer, PathAccessError, UnregisteredTarget


class A(object):
    pass

class B(object):
    pass

class C(A):
    pass

class D(B):
    pass

class E(C, D, A):
    pass

class F(E):
    pass


def test_types_leave_one_out():
    ALL_TYPES = [A, B, C, D, E, F]
    for cur_t in ALL_TYPES:

        glommer = Glommer(register_default_types=True)
        for t in ALL_TYPES:
            if t is cur_t:
                continue
            glommer.register(t, getattr)

        obj = cur_t()
        assert glommer._get_closest_type(obj) == obj.__class__.mro()[1]

        if cur_t is E:
            assert glommer._get_closest_type(obj) is C  # sanity check

    return


def test_types_bare():
    glommer = Glommer(register_default_types=False)

    assert glommer._get_closest_type(object()) is None

    # test that bare glommers can't glom anything
    with pytest.raises(UnregisteredTarget):
        glommer.glom(object(), {'object_repr': '__class__.__name__'})

    with pytest.raises(UnregisteredTarget):
        glommer.glom([{'hi': 'hi'}], ['hi'])

    glommer.register(object, getattr)

    # check again that registering object for 'get' doesn't change the
    # fact that we don't have iterate support yet
    with pytest.raises(UnregisteredTarget):
        glommer.glom([{'hi': 'hi'}], ['hi'])


    return


def test_invalid_register():
    glommer = Glommer()
    with pytest.raises(TypeError):
        glommer.register(1)
    return


def test_duck_register():
    class LilRanger(object):
        def __init__(self):
            self.lil_list = list(range(5))

        def __iter__(self):
            return iter(self.lil_list)

    glommer = Glommer(register_default_types=False)

    target = LilRanger()

    with pytest.raises(UnregisteredTarget):
        float_range = glommer.glom(target, [float])

    glommer.register(LilRanger)

    float_range = glommer.glom(target, [float])

    assert float_range == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_bypass_getitem():
    target = list(range(3)) * 3

    with pytest.raises(TypeError):
        glom.glom(target, 'count')

    res = glom.glom(target, lambda list_obj: list_obj.count(1))

    assert res == 3
