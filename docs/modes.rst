``glom`` Modes
==============

A mode determines how python built-in
data structures are evaluated.  A mode is used
similar to a spec: whatever python data structure
is passed to the mode class init will be evaluated
under that mode.

Modes do not change the behavior of `T`, or spec classes;
they only modify `dict`, `tuple`, `list`, etc.

Once set, the mode remains in place until it is
overridden by another mode.

The default behavior of glom is the :class:`~glom.Auto`
mode.  The next most common mode is :class:`~glom.Fill`.

custom modes
------------

A mode is a spec which sets `scope[MODE]` to a function
which accepts target, spec, and scope and returns a result.

For example, here is an abbreviated version of :class:`~glom.Fill`


.. code-block:: python

    class Fill(object):
        def __init__(self, spec):
            self.spec = spec

        def glomit(self, target, scope):
            scope[MODE] = _fill
            return scope[glom](target, self.spec, scope)

    def _fill(target, spec, scope):
        recurse = lambda val: scope[glom](target, val, scope)
        if type(spec) is dict:
            return {recurse(key): recurse(val)
                    for key, val in spec.items()}
        if type(spec) in (list, tuple, set, frozenset):
            result = [recurse(val) for val in spec]
            if type(spec) is list:
                return result
            return type(spec)(result)
        if callable(spec):
             return spec(target)
        return spec


