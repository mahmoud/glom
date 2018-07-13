'''
this module contains Specs that perform mutations
'''
from .core import _TType, _T_PATHS, _t_child, _t_eval, Path, T, S, Spec, BaseSpec, glom


# TODO: how to get this into default spec registry?
# options:
#   1- have a different registry here
#   2- just eat the circularity
#   3- move Assign back to core.py (but that is getting large)
#   4- add some default behavior -- "if it is an instance of BaseSpec, call handle"
class Assign(BaseSpec):
    def __init__(self, path, val):
        if isinstance(path, basestring):
            path = Path(*path.split('.'))
        if not isinstance(path, (Path, _TType)):
            raise TypeError('path argument must be a . delimeted string, Path, T, or S')
        if type(path) is Path:
            path = path.path_t
        segs = _T_PATHS[path]
        if len(segs) < 3:
            raise ValueError('path must have at least one element')
        cur = segs[0]
        assert cur in (T, S)
        for i in range(1, len(segs) - 2, 2):
            cur = _t_child(segs[i], segs[i + 1])
        self.t = cur
        self.op, self.arg = segs[-2:]
        if self.op not in '[.P':
            raise ValueError('last path of path must be setattr or setitem')
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
