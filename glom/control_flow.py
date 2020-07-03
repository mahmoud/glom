"""
Control flow primitives of glom.
"""

from glom import glom, GlomError


_MISSING = object()


class Switch(object):
    """
    Switch implements control flow similar to the switch
    statement added in python 3.10

    The constructor accepts a dictionary of {keyspec: valspec}
    or a list of [(keyspec, valspec)]; keyspecs are tried
    against the current target in order.  The keyspecs
    are tried in order; if they keyspec raises GlomError,
    the next keyspec is tried.  Once a keyspec succeeds,
    the corresponding valspec is evaluated and returned.

    If no keyspec succeeds, a GlomError is raised, or
    the default is returned if one was specified.
    """
    def __init__(self, cases, default=_MISSING):
        if type(cases) is dict:
            cases = list(cases.items())
        if type(cases) is not list:
            raise TypeError(
                "cases must be {keyspec: valspec} or "
                "[(keyspec, valspec)] not {}".format(type(cases)))
        self.cases = cases
        # glom.match(cases, Or([(object, object)], dict))
        # start dogfooding ^
        self.default = default

    def glomit(self, target, scope):
        for keyspec, valspec in self.cases:
            try:
                scope[glom](target, keyspec, scope)
                break
            except GlomError:
                pass
        else:
            if self.default is not _MISSING:
                return default
            raise GlomError("no matches for target in Switch")
        return scope[glom](target, valspec, scope)

    def __repr__(self):
        return "Switch(" + repr(self.cases) + ")"
