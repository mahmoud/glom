"""
creating and assigning local variables
"""
from glom import UP, ROOT, glom


class _Binding(object):
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

    def _write_to(self, target, scope):
        if type(self.binding) is str:
            scope[self.binding] = target
        else:
            scope.update({
                k: scope[glom](target, v, scope) for k, v in self.binding.items()})


class Name(_Binding):
    """
    Name("var") -- assigns var to local scope
    so that it can be accessed with S["var"]
    """
    def glomit(self, target, scope):
        self._write_to(target, scope[UP])
        return target


class Globals(_Binding):
    """
    Global("var") -- assign var to the global scope
    """
    def glomit(self, target, scope):
        self._write_to(target, scope[ROOT])
        return target
