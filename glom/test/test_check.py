
from glom import glom, Check, GlomCheckError, Coalesce, OMIT, T


def test_check_basic():
    def _err(f):
        try:
            f()
            assert False  # pragma: no cover
        except GlomCheckError:
            pass
    target = [{'id': 0}, {'id': 1}]
    assert glom([0, OMIT], [T]) == [0]
    assert glom(target, ([Coalesce(Check('id', equal_to=0), default=OMIT)], T[0])) == {'id': 0}
    assert glom(target, ([Check('id', equal_to=0, default=OMIT)], T[0])) == {'id': 0}
    assert glom([1, 'a'], [Check(type=str, default=OMIT)]) == ['a']
    assert glom([1, 'a'], [Check(type=(str, int))]) == [1, 'a']
    assert glom([1, 'a'], [Check(instance_of=str, default=OMIT)]) == ['a']
    assert glom([1, 'a'], [Check(instance_of=(str, int))]) == [1, 'a']
    _err(lambda: glom(1, Check(type=str)))
    _err(lambda: glom(1, Check(type=(str, bool))))
    _err(lambda: glom(1, Check(instance_of=str)))
    _err(lambda: glom(1, Check(instance_of=(str, bool))))
    _err(lambda: glom(1, Check(equal_to=0)))
    _err(lambda: glom(1, Check(one_of=(0,))))
    _err(lambda: glom(1, Check(one_of=(0, 2))))
