"""
High performance Cythonized form of Path and T classes.
"""
from glom.core import *



class Path(object):
    """Path objects specify explicit paths when the default
    ``'a.b.c'``-style general access syntax won't work or isn't
    desirable. Use this to wrap ints, datetimes, and other valid
    keys, as well as strings with dots that shouldn't be expanded.

    >>> target = {'a': {'b': 'c', 'd.e': 'f', 2: 3}}
    >>> glom(target, Path('a', 2))
    3
    >>> glom(target, Path('a', 'd.e'))
    'f'

    Paths can be used to join together other Path objects, as
    well as :data:`~glom.T` objects:

    >>> Path(T['a'], T['b'])
    T['a']['b']
    >>> Path(Path('a', 'b'), Path('c', 'd'))
    Path('a', 'b', 'c', 'd')

    Paths also support indexing and slicing, with each access
    returning a new Path object:

    >>> path = Path('a', 'b', 1, 2)
    >>> path[0]
    Path('a')
    >>> path[-2:]
    Path(1, 2)
    """
    def __init__(self, *path_parts):
        if not path_parts:
            self.path_t = T
            return
        if isinstance(path_parts[0], TType):
            path_t = path_parts[0]
            offset = 1
        else:
            path_t = T
            offset = 0
        for part in path_parts[offset:]:
            if isinstance(part, Path):
                part = part.path_t
            if isinstance(part, TType):
                sub_parts = _T_PATHS[part]
                if sub_parts[0] is not T:
                    raise ValueError('path segment must be path from T, not %r'
                                     % sub_parts[0])
                i = 1
                while i < len(sub_parts):
                    path_t = _t_child(path_t, sub_parts[i], sub_parts[i + 1])
                    i += 2
            else:
                path_t = _t_child(path_t, 'P', part)
        self.path_t = path_t

    _CACHE = {True: {}, False: {}}
    _MAX_CACHE = 10000
    _STAR_WARNED = False

    @classmethod
    def from_text(cls, text):
        """Make a Path from .-delimited text:

        >>> Path.from_text('a.b.c')
        Path('a', 'b', 'c')

        """
        def create():
            segs = text.split('.')
            if PATH_STAR:
                segs = [
                    _T_STAR if seg == '*' else
                    _T_STARSTAR if seg == '**' else seg
                    for seg in segs]
            elif not cls._STAR_WARNED:
                if '*' in segs or '**' in segs:
                    warnings.warn(
                        "'*' and '**' will changed behavior in a future glom version."
                        " Recommend switch to T['*'] or T['**'].")
                    cls._STAR_WARNED = True
            return cls(*segs)

        cache = cls._CACHE[PATH_STAR]  # remove this when PATH_STAR is default
        if text not in cache:
            if len(cache) > cls._MAX_CACHE:
                return create()
            cache[text] = create()
        return cache[text]

    def glomit(self, target, scope):
        # The entrypoint for the Path extension
        return _t_eval(target, self.path_t, scope)

    def __len__(self):
        return (len(_T_PATHS[self.path_t]) - 1) // 2

    def __eq__(self, other):
        if type(other) is Path:
            return _T_PATHS[self.path_t] == _T_PATHS[other.path_t]
        elif type(other) is TType:
            return _T_PATHS[self.path_t] == _T_PATHS[other]
        return False

    def __ne__(self, other):
        return not self == other

    def values(self):
        """
        Returns a tuple of values referenced in this path.

        >>> Path(T.a.b, 'c', T['d']).values()
        ('a', 'b', 'c', 'd')
        """
        cur_t_path = _T_PATHS[self.path_t]
        return cur_t_path[2::2]

    def items(self):
        """
        Returns a tuple of (operation, value) pairs.

        >>> Path(T.a.b, 'c', T['d']).items()
        (('.', 'a'), ('.', 'b'), ('P', 'c'), ('[', 'd'))

        """
        cur_t_path = _T_PATHS[self.path_t]
        return tuple(zip(cur_t_path[1::2], cur_t_path[2::2]))

    def startswith(self, other):
        if isinstance(other, basestring):
            other = Path(other)
        if isinstance(other, Path):
            other = other.path_t
        if not isinstance(other, TType):
            raise TypeError('can only check if Path starts with string, Path or T')
        o_path = _T_PATHS[other]
        return _T_PATHS[self.path_t][:len(o_path)] == o_path

    def from_t(self):
        '''return the same path but starting from T'''
        t_path = _T_PATHS[self.path_t]
        if t_path[0] is S:
            new_t = TType()
            _T_PATHS[new_t] = (T,) + t_path[1:]
            return Path(new_t)
        return self

    def __getitem__(self, i):
        cur_t_path = _T_PATHS[self.path_t]
        try:
            step = i.step
            start = i.start if i.start is not None else 0
            stop = i.stop

            start = (start * 2) + 1 if start >= 0 else (start * 2) + len(cur_t_path)
            if stop is not None:
                stop = (stop * 2) + 1 if stop >= 0 else (stop * 2) + len(cur_t_path)
        except AttributeError:
            step = 1
            start = (i * 2) + 1 if i >= 0 else (i * 2) + len(cur_t_path)
            if start < 0 or start > len(cur_t_path):
                raise IndexError('Path index out of range')
            stop = ((i + 1) * 2) + 1 if i >= 0 else ((i + 1) * 2) + len(cur_t_path)

        new_t = TType()
        new_path = cur_t_path[start:stop]
        if step is not None and step != 1:
            new_path = tuple(zip(new_path[::2], new_path[1::2]))[::step]
            new_path = sum(new_path, ())
        _T_PATHS[new_t] = (cur_t_path[0],) + new_path
        return Path(new_t)

    def __repr__(self):
        return _format_path(_T_PATHS[self.path_t][1:])

