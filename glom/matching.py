"""
Contains code associated with implementing "match" mode

match mode tends to build expression trees by conjoining
together matches with And / &, Or / |

example use cases:

filter list on condition (e.g. >= 10)
[Coalesce(Match(int & (M >= 10)), default=SKIP)]

ensure that dictionary values are all strings
Match({DEFAULT: str})
"""
from boltons.typeutils import make_sentinel

import weakref

from .core import GlomError, glom


class GlomMatchError(GlomError): pass
class GlomTypeMatchError(GlomError, TypeError): pass


class Match(object):
    """
    switch to "match" mode
    """
    def __init__(self, spec):
        self.spec = spec

    def glomit(self, target, scope):
        scope[glom] = _glom_match
        return scope[glom](target, self.spec, scope)


DEFAULT = make_sentinel("DEFAULT")
DEFAULT.__doc__ = """
DEFAULT is used to represent keys that are not otherwise matched
in a dict in match mode
"""

class _Comparable(object):
    """
    abstract class for binary operations
    """
    def __eq__(self, other):
        return Equal(self, other)

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)


class MType(object):
    """
    Similar to T, but for matching
    """
    __slots__ = ('__weakref__',)

    def __eq__(self, other):
        return _m_child(self, '=', other)

    def __and__(self, other):
        return _m_child(self, '&', other)

    def __or__(self, other):
        return _m_child(self, '|', other)



_M_EXPRS = weakref.WeakKeyDictionary()

M = MType()

_M_EXPRS[M] = (M,)


def _glom_match(target, spec, scope):
    scope = scope.new_child()
    scope[T] = target
    scope[Spec] = spec

    if callable(getattr(spec, 'glomit', None)):
        return spec.glomit(target, scope)
    elif isinstance(spec, type):
        if not isinstance(target, spec):
            raise GlomTypeMatchError(type(target), spec)
    elif isinstance(spec, dict):

        return _handle_dict(target, spec, scope)
    elif isinstance(spec, list):
        return _handle_list(target, spec, scope)
    elif isinstance(spec, tuple):
        return _handle_tuple(target, spec, scope)
    elif isinstance(spec, basestring):
        return Path.from_text(spec).glomit(target, scope)
    elif callable(spec):
        return spec(target)

    raise TypeError('expected spec to be dict, list, tuple, callable, string,'
                    ' or other Spec-like type, not: %r' % (spec,))

