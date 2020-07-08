``glom`` Modes
==============

.. note::

   Be sure to read ":doc:`custom_spec_types`" before diving into the
   deep details below.

A glom "mode" determines how Python built-in data structures are
evaluated. Think of it like a dialect for how :class:`dict`,
:class:`tuple`, :class:`list`, etc., are interpreted in a spec. Modes
do not change the behavior of `T`, or many other core
specifiers. Modes are one of the keys to keeping glom specs short and
readable.

A mode is used similar to a spec: whatever Python data structure is
passed to the mode type constructor will be evaluated under that
mode. Once set, the mode remains in place until it is overridden by
another mode.

glom only has a few modes:

  1. :class:`~glom.Auto` - The default glom behavior, used for data
     transformation, with the spec acting as a template.
  2. :class:`~glom.Fill` - A variant of the default transformation
     behavior; preferring to "fill" containers instead of
     iterating, chaining, etc.
  3. :class:`~glom.Match` - Treats the spec as a pattern, checking
     that the target matches.

Adding a new mode is relatively rare, but when it comes up this
document includes relevant details.


Writing custom Modes
--------------------

A mode is a spec which sets ``scope[MODE]`` to a function which
accepts ``target``, ``spec``, and ``scope`` and returns a result, a
signature very similar to the top-level :func:`~glom.glom` method
itself.

For example, here is an abbreviated version of the :class:`~glom.Fill`
mode:


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

Like any other :doc:`Specifier Type <custom_spec_types>`, ``Fill`` has
a ``glomit()`` method, and this method sets the ``MODE`` key in the
:ref:`glom scope <glom_scope>` to our ``_fill`` function. The name
itself doesn't matter, but the signature must match exactly:
``(target, spec, scope)``.

As mentioned above, custom modes are relatively rare for glom. If you
write one, `let us know <https://github.com/mahmoud/glom/issues>`_!
