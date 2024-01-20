
from glom import glom


class Seq(object):
    "Applies a list of specs to a single target, returning a list of results"
    def __init__(self, *subspecs):
        self.subspecs = subspecs

    def glomit(self, target, scope):
        return [scope[glom](target, spec, scope) for spec in self.subspecs]

output = glom('1', Seq(float, int))

assert output == [1.0, 1]
