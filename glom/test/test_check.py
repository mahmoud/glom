
from pytest import raises

from glom import glom, Check, GlomCheckError, Coalesce, OMIT, T


def test_check_basic():
    assert glom([0, OMIT], [T]) == [0]  # sanity check OMIT

    target = [{'id': 0}, {'id': 1}]
    assert glom(target, ([Coalesce(Check('id', equal_to=0), default=OMIT)], T[0])) == {'id': 0}
    assert glom(target, ([Check('id', equal_to=0, default=OMIT)], T[0])) == {'id': 0}

    target = [1, 'a']
    assert glom(target, [Check(type=str, default=OMIT)]) == ['a']
    assert glom(target, [Check(type=(str, int))]) == [1, 'a']
    assert glom(target, [Check(instance_of=str, default=OMIT)]) == ['a']
    assert glom(target, [Check(instance_of=(str, int))]) == [1, 'a']

    target = ['1']
    assert glom(target, [Check(validate=(int, float))])
    assert glom(target, [Check()])  # bare check does a truthy check

    failing_checks = [(1, Check(type=str)),
                      (1, Check(type=(str, bool))),
                      (1, Check(instance_of=str)),
                      (1, Check(instance_of=(str, bool))),
                      (1, Check(equal_to=0)),
                      (1, Check(one_of=(0,))),
                      (1, Check(one_of=(0, 2))),
                      ('-3.14', Check(validate=int)),
                      ('', Check(validate=lambda x: False)),]

    for target, check in failing_checks:
        with raises(GlomCheckError):
            glom(target, check)


def test_check_signature():
    with raises(ValueError):
        Check(instance_of=())
    with raises(ValueError):
        Check(type=())

    with raises(TypeError):
        Check(fake_kwarg=True)

    with raises(ValueError):
        Check(one_of=1)
    with raises(ValueError):
        Check(one_of=())
    with raises(TypeError):
        Check(one_of=(1, 2), equal_to=3)

    with raises(ValueError):
        Check(validate='bad, not callable, value')
