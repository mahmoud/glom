Frequently Asked Questions
==========================

Paradigm shifts always raise a question or two.

.. contents:: Contents
   :local:

What does "glom" mean?
----------------------

"glom" is short for "conglomerate", which means "gather into a compact
form", coming from the Latin "glom-" meaning *ball*, like *globe*.

glom can be used as a noun or verb. A developer might say, "I glommed
together this API response." An astronomer might say, "these gloms of
space dust are forming planets and comets."

Got some data you need to transform? **glom it! ☄️**

Any other glom terminology worth knowing?
-----------------------------------------

A couple of conventional terms that help navigate around glom's
semantics:

* **target** - ``glom`` operates on a variety of inputs, so we simply
  refer to the object being accessed (i.e., the first argument to
  ``glom()``) as the "target"
* **spec** - *(aka "glomspec")* The accompanying template used to
  specify the structure and sources of the output.
* **output** - The value retrieved or created and returned by
  ``glom()``.

All of these can be seen in the conventional call to :func:`~glom.glom`::

  output = glom(target, spec)

Nothing too wild, but these standard terms really do help clarify the
complex situations ``glom`` was built to handle.

Other glom tips?
----------------

Just a few (for now):

* Specs don't have to live in the glom call. You can put them
  anywhere. Commonly-used specs work as class attributes and globals.
* Using glom's declarative approach does wonders for code coverage,
  much like `attrs`_ and `schema`_, both of which go great
  with ``glom``.
* Advanced tips
    * glom is designed to support all of Python's built-ins as targets,
      and is readily extensible to other types and special handling, through
      :func:`~glom.register()`.
    * If you're trying to minimize global state, consider
      instantiating your own :class:`~glom.Glommer` object to
      encapsulate any type registration changes.

If you've got more tips or patterns, `send them our way`_!

.. _attrs: https://github.com/python-attrs/attrs
.. _schema: https://github.com/keleshev/schema
.. _send them our way: https://github.com/mahmoud/glom/issues

Why not just write more Python?
-------------------------------

The answer is more than just DRY ("Don't Repeat Yourself").

Here on the glom team, we're big fans of Python. Have been for
years. In fact, Python is one of a tiny handful of languages that
could support something as powerful as glom.

But not all Python code is the same. We built glom to replace the kind
of Python that is about as un-Pythonic as code gets: simultaneously
fluffy, but also fragile. Simple transformations requiring countless
lines.

Before glom, the "right" way to write this transformation code was
verbose. Whether trying to fetch values nested within objects that may
contain attributes set to ``None``, or performing a list comprehension
which may raise an exception, the *correct* code was many lines of
repetitious ``try-except`` blocks with a lot of hand-written exception
messages.

Written any more compactly, this Python would produce failures
expressed in errors too low-level to associate with the higher-level
transformation.

So the glom-less code was hard to change, hard to debug, or
both. ``glom`` specifications are none of the above, thanks to
meaningful, high-level error messages, a :class:`a built-in debugging
facility <glom.Inspect>`, and a compact, composable design.

In short, thanks to Python, glom can provide a Pythonic solution for
those times when pure Python wasn't Pythonic enough.


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

Does Python need a null-coalescing operator?
--------------------------------------------

Not technically a glom question, but it is frequently_ asked_!

`Null coalescing operators`_ traverse nested objects and return null
(or ``None`` for us) on the first null or non-traversable object,
depending on implementation.

It's basically a compact way of doing a deep :func:`getattr()` with a
default set to ``None``.

Suffice to say that ``glom(target, T.a.b.c, default=None)`` achieves
this with ease, but I still want to revisit the question, since it's
part of what got me thinking about ``glom`` in the first place.

First off, working in PayPal's SOA environment, my team dealt with
literally tens of thousands of service objects, with object
definitions (from other teams) nested so deep as to make an
80-character line length laughable.

But null coalescing wouldn't have helped, because in most of those
cases ``None`` wasn't what we needed. We needed a good, automatically
generated error message when a deeply-nested field wasn't accessible. Not
``NoneType has no attribute 'x'``, but not plain old ``None`` either.

To solve this, I wrote my share of deep-gets before ``glom``,
including the open-source `boltons.iterutils.get_path()`_. For
whatever reason, it took me years of usage to realize just how often
the deep-gets were coupled with the other transformations that
``glom`` enables. Now, I can never go back to a simple deep-get.

Another years-in-the-making observation, from my time doing JavaScript
then PHP then Django templates: all were much more lax on typing than
Python. Not because of a fierce belief in weak types, though. More
because when you're templating, it's inherently safer to return a
blank value on lookup failures. You're so close to text formats that
this default achieves a pretty desirable result. While implicitly
doing this isn't my cup of tea, and ``glom`` opts for explicit
:class:`~glom.Coalesce` specifiers, this connection contributed to the
concept of ``glom`` as an "object templating" system.




.. _frequently: https://mail.python.org/pipermail/python-ideas/2015-September/036289.html
.. _asked: https://mail.python.org/pipermail/python-ideas/2016-November/043517.html
.. _Null coalescing operators: https://en.wikipedia.org/wiki/Null_coalescing_operator
.. _boltons.iterutils.get_path(): http://boltons.readthedocs.io/en/latest/iterutils.html#boltons.iterutils.get_path
