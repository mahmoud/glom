Frequently Asked Questions
==========================

Paradigm shifts always raise a question or two.

.. contents:: Contents
   :local:


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
