"""
creating and assigning local variables
"""
from glom import glom


class Let(object):
    """
    Let("var").over(subspec) -- assigns var to
    scope that subspec executes under

    other form is Let(foo=spec1, bar=spec2).over(subspec)
    """
    def __init__(self, *a, **kw):
        if a:
            assert not kw
            assert len(a) == 1
            a0 = a[0]
            assert type(a0) is str
            self.binding = a0
        if kw:
            assert not a
            self.binding = kw

    def over(self, subspec):
        return _LetOver(self, subspec)

    def _write_to(self, target, scope):
        if type(self.binding) is str:
            scope[self.binding] = target
        else:
            scope.update({
                k: scope[glom](target, v, scope) for k, v in self.binding.items()})


class _LetOver(object):
    def __init__(self, let, subspec):
        self.let, self.subspec = let, subspec

    def glomit(self, target, scope):
        self.let._write_to(target, scope)
        if type(self.binding) is str:
            scope[self.binding] = target
        else:
            scope.update({
                k: scope[glom](target, v, scope) for k, v in self.binding.items()})
        return scope[glom](target, self.subspec, scope)
