
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

    try:
        glommer.glom([{'hi': 'hi'}], ['hi'])
    except UnregisteredTarget as ute:
        assert not ute.type_map
        assert 'without registering' in str(ute)
    else:
        assert False, 'expected an UnregisteredTarget exception'

    glommer.register(object, getattr)

    # check again that registering object for 'get' doesn't change the
    # fact that we don't have iterate support yet
    try:
        glommer.glom([{'hi': 'hi'}], ['hi'])
    except UnregisteredTarget as ute:
        assert str(ute) == "target type 'list' not registered for 'iterate', expected one of registered types: ()"
    else:
        assert False, 'expected an UnregisteredTarget exception'
    return


def test_invalid_register():
    glommer = Glommer()
    with pytest.raises(TypeError):
        glommer.register(1)
    return


def test_exact_register():
    glommer = Glommer(register_default_types=False)

    class BetterList(list):
        pass

    glommer.register(BetterList, iterate=iter, exact=True)

    expected = [0, 2, 4]
    value = glommer.glom(BetterList(range(3)), [lambda x: x * 2])
    assert value == expected

    with pytest.raises(UnregisteredTarget):
        glommer.glom(list(range(3)), [lambda x: x * 2])

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

    glommer = Glommer()  # now with just defaults
    float_range = glommer.glom(target, [float])
    assert float_range == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_bypass_getitem():
    target = list(range(3)) * 3

    with pytest.raises(PathAccessError):
        glom.glom(target, 'count')

    res = glom.glom(target, lambda list_obj: list_obj.count(1))

    assert res == 3


def test_iter_set():
    some_ints = set(range(5))
    some_floats = glom.glom(some_ints, [float])

    assert sorted(some_floats) == [0.0, 1.0, 2.0, 3.0, 4.0]

    # now without defaults
    glommer = Glommer(register_default_types=False)
    glommer.register(set, iterate=iter)
    some_floats = glom.glom(some_ints, [float])

    assert sorted(some_floats) == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_iter_str():
    # check that strings are not iterable by default, one of the most
    # common sources of bugs
    glom_buddy = 'kurt'

    with pytest.raises(UnregisteredTarget):
        glom.glom(glom_buddy, {'name': [glom_buddy]})

    # also check that someone can override this

    glommer = Glommer()
    glommer.register(str, iterate=iter)
    res = glommer.glom(glom_buddy, {'name_chars_for_some_reason': [str]})
    assert len(res['name_chars_for_some_reason']) == 4

    # the better way, for any dissenter reading this

    assert glom.glom(glom_buddy, {'name_chars': list}) == {'name_chars': ['k', 'u', 'r', 't']}

    # and for the really passionate: how about making strings
    # non-iterable and just giving them a .chars() method that returns
    # a list of single-character strings.
