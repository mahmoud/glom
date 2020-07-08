"""
Control flow primitives of glom.
"""

from glom import glom, GlomError
from .core import bbrepr, LAST_CHILD_SCOPE


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
                "cases must be {{keyspec: valspec}} or "
                "[(keyspec, valspec)] not {}".format(type(cases)))
        self.cases = cases
        # glom.match(cases, Or([(object, object)], dict))
        # start dogfooding ^
        self.default = default
        if not cases and self.default is _MISSING:
            raise ValueError('Switch() without cases or default will always error')

    def glomit(self, target, scope):
        for keyspec, valspec in self.cases:
            try:
                scope[glom](target, keyspec, scope)
            except GlomError as ge:
                continue
            scope = scope[LAST_CHILD_SCOPE]  # valspec child of keyspec so e.g. var capture
            return scope[glom](target, valspec, scope)
        if self.default is not _MISSING:
            return self.default
        raise GlomError("no matches for target in Switch")

    def __repr__(self):
        return "Switch(" + bbrepr(self.cases) + ")"
