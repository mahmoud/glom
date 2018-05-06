Frequently Asked Questions
==========================

Paradigm shifts always raise a question or two.

.. contents:: Contents
   :local:

What does "glom" mean?
----------------------

"glom" is short for "conglomerate", which means "gather into a compact
form".

glom can be used as a noun or verb. A developer might say, "I glommed
together this API response." An astronomer might say, "space dust is
forming gloms, creating planets and comets."

Got some data you need to transform? **glom it! ☄️**

Why not just write more Python?
-------------------------------

The answer is more than just DRY ("Don't Repeat Yourself").

Here on the glom team, we're big fans of Python. Not only is glom
written in it, we've used it for virtually everything. In fact, Python
is one of a very small handful of languages that could support
something as powerful as glom.

But not all Python code is the same. We built glom to replace the kind
of code that is about as un-Pythonic as code gets: simultaneously
fluffy, but also fragile. Many lines achieving a relatively
easy-to-envision transformation.

Up until now, the "right" way to write this transformation code was
verbose. Whether trying to access across objects that may contain
attributes set to None, or performing a list comprehension which may
raise an exception, the correct code was many lines of repetitious
``try-except`` blocks. Written any more compact, and failures
would be expressed in errors too low-level to associate with the
higher-level transformation.

So the glom-less code was hard to change, hard to debug, or
both. ``glom`` specifications are none of the above, thanks to
meaningful, high-level error messages, a :class:`a built-in debugging
facility <glom.Inspect>`, and a compact, composable design.

In short, thanks to Python, glom provides Pythonic solutions in
specific cases when pure-Python might break down.


How does glom work?
-------------------

The core conceptual engine of glom is a very simple recursive loop. It
could fit on a business card. OK maybe a postcard.

In fact, here it is, in literate form, modified from this `early point
in glom history`_:

.. code-block:: python

    def glom(target, spec):

        # if the spec is a string or a Path, perform a deep-get on the target
        if isinstance(spec, (basestring, Path)):
            return _get_path(target, spec)

        # if the spec is callable, call it on the target
        elif callable(spec):
            return spec(target)

        # if the spec is a dict, assign the result of
        # the glom on the right to the field key on the left
        elif isinstance(spec, dict):
            ret = {}
            for field, subspec in spec.items():
               ret[field] = glom(target, subspec)
            return ret

        # if the spec is a list, run the spec inside the list on every
        # element in the list and return the new list
        elif isinstance(spec, list):
            subspec = spec[0]
            iterator = _get_iterator(target)
            return [glom(t, subspec) for t in iterator]

        # if the spec is a tuple of specs, chain the specs by running the
        # first spec on the target, then running the second spec on the
        # result of the first, and so on.
        elif isinstance(spec, tuple):
            res = target
            for subspec in spec:
                res = glom(res, subspec)
            return res
        else:
            raise TypeError('expected one of the above types')


.. _early point in glom history: https://github.com/mahmoud/glom/blob/186757b47af3d33901df4bf715874b5f3c781d8f/glom/__init__.py#L74-L91