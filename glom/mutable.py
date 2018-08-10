'''
this module contains Specs that perform mutations
'''
import operator

from .core import Path, T, S, Spec, glom, UnregisteredTarget
from .core import _TType, _T_PATHS, _t_child, _t_eval, _DEFAULT_SCOPE, TargetRegistry

try:
    basestring
except NameError:
    basestring = str


if getattr(__builtins__, '__dict__', None):
    # pypy's __builtins__ is a module, as is CPython's REPL, but at
    # normal execution time it's a dict?
    __builtins__ = __builtins__.__dict__


class Assign(object):
    def __init__(self, path, val):
        if isinstance(path, basestring):
            path = Path(*path.split('.')).path_t
        elif type(path) is Path:
            path = path.path_t
        elif not isinstance(path, _TType):
            raise TypeError('path argument must be a .-delimited string, Path, T, or S')

        segs = _T_PATHS[path]
        if len(segs) < 3:
            raise ValueError('path must have at least one element')

        cur = segs[0]
        assert cur in (T, S)
        for i in range(1, len(segs) - 2, 2):
            cur = _t_child(cur, segs[i], segs[i + 1])
        self.t = cur
        self.op, self.arg = segs[-2:]
        if self.op not in '[.P':  # pragma: no cover
            # maybe if we add null-coalescing this should do something?
            raise ValueError('last part of path must be setattr or setitem')
        self.val = val

    def glomit(self, target, scope):
        if type(self.val) is Spec:
            val = scope[glom](target, self.val, scope)
        else:
            val = self.val
        dest = _t_eval(target, self.t, scope)
        # TODO: forward-detect immutable dest?
        if self.op == '[':
            dest[self.arg] = val
        elif self.op == '.':
            setattr(dest, self.arg, val)
        elif self.op == 'P':
            assign = scope[TargetRegistry].get_handler('assign', dest)
            if not assign:
                raise UnregisteredTarget('assign', type(dest),
                                         scope[TargetRegistry].get_type_map('assign'),
                                         path=scope[Path])
            try:
                assign(dest, self.arg, val)
            except Exception as e:
                raise TypeError('failed to assign on instance of type %r at %r (got %r)'
                                % (dest.__class__.__name__, Path(*scope[Path]), e))

        return target


def assign(obj, path, val):
    return glom(obj, Assign(path, val))


_ALL_BUILTIN_TYPES = [v for v in __builtins__.values() if isinstance(v, type)]
_BUILTIN_BASE_TYPES = [v for v in _ALL_BUILTIN_TYPES
                       if not issubclass(v, tuple([t for t in _ALL_BUILTIN_TYPES
                                                   if t not in (v, type, object)]))]
_UNASSIGNABLE_BASE_TYPES = tuple(set(_BUILTIN_BASE_TYPES)
                                 - set([dict, list, BaseException, object, type]))


def _set_sequence_item(target, idx, val):
    target[int(idx)] = val

# how to get this into the target registry? just put it in the root
# one?  autorun autodiscovery over known types when adding a new
# autodiscovery probably just let autodiscovery be totally global, and
# remove the ability to not register autodiscoverers.
def _assign_autodiscover(type_obj):
    # TODO: issubclass or "in"?
    if issubclass(type_obj, _UNASSIGNABLE_BASE_TYPES):
        return False

    if callable(getattr(type_obj, '__setitem__', None)):
        if callable(getattr(type_obj, 'index', None)):
            return _set_sequence_item
        return operator.setitem

    return setattr


_DEFAULT_SCOPE[TargetRegistry].register_op('assign', _assign_autodiscover, exact=False)
