'''
this module contains Specs that perform mutations
'''
import operator

from .core import _TType, _T_PATHS, _t_child, _t_eval, Path, T, S, Spec, BaseSpec, glom

from . import core

if 'basestring' in core.__dict__:
    from .core import basestring

# TODO: how to get this into default spec registry?
# options:
#   1- have a different registry here
#   2- just eat the circularity
#   3- move Assign back to core.py (but that is getting large)
#   4- add some default behavior -- "if it is an instance of BaseSpec, call handle"
#   5- class decorator that does a bit of checking as well as the registration
class Assign(BaseSpec):
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
        if self.op not in '[.P':  # maybe if we add null-coalescing this should do something?
            raise ValueError('last part of path must be setattr or setitem')
        self.val = val

    def glomit(self, target, scope):
        if type(self.val) is Spec:
            val = scope[glom](target, self.val, scope)
        else:
            val = self.val
        dest = _t_eval(self.t, target, scope)
        # TODO: forward-detect immutable dest?
        if self.op == '[':
            dest[self.arg] = val
        elif self.op == '.':
            setattr(dest, self.arg, val)
        elif self.op == 'P':
            if type(dest) is dict:
                dest[self.arg] = val
            elif type(dest) is list:
                dest[int(self.arg)] = val
            else:
                setattr(dest, self.arg, val)
        return target


def assign(obj, path, val):
    return glom(obj, Assign(path, val))


_ALL_BUILTIN_TYPES = [v for v in __builtins__.__dict__.values() if isinstance(v, type)]
_BUILTIN_BASE_TYPES = [v for v in _ALL_BUILTIN_TYPES
                       if not issubclass(v, tuple([t for t in _ALL_BUILTIN_TYPES
                                                   if t not in (v, type, object)]))]
_UNASSIGNABLE_BASE_TYPES = tuple(set(_BUILTIN_BASE_TYPES) - set([dict, list, BaseException]))


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
