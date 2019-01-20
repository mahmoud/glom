``glom`` API reference
======================

.. automodule:: glom.core

.. contents:: Contents
   :local:

.. _glom-func:

The ``glom`` Function
---------------------

Where it all happens. The reason for the season. The eponymous function, ``glom``.

.. autofunction:: glom.glom


Specifier Types
---------------

Basic glom specifications consist of ``dict``, ``list``, ``tuple``,
``str``, and ``callable`` objects. However, as data calls for more
complicated interactions, ``glom`` provides specialized specifier
types that can be used with the basic set of Python builtins.

.. autoclass:: glom.Path
.. autoclass:: glom.Literal
.. autoclass:: glom.Spec

Advanced Specifiers
-------------------

The specification techniques detailed above allow you to do pretty
much everything glom is designed to do. After all, you can always
define and insert a function or ``lambda`` into almost anywhere in the
spec?

Still, for even more specification readability and improved error
reporting, glom has a few more tricks up its sleeve.

Conditional access and defaults with Coalesce
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Data isn't always where or what you want it to be. Use these
specifiers to declare away overly branchy procedural code.

.. autoclass:: glom.Coalesce

.. autodata:: glom.SKIP
.. autodata:: glom.STOP

Target mutation with Assign
^^^^^^^^^^^^^^^^^^^^^^^^^^^

*New in glom 18.3.0*

Most of glom's API design defaults to safely copying your data. But
such caution isn't always justified.

When you already have a large or complex bit of nested data that you
are sure you want to modify in-place, glom has you covered, with the
:func:`~glom.assign` function, and the :func:`~glom.Assign` specifier
type.

.. autofunction:: glom.assign

.. autoclass:: glom.Assign


Reducing lambda usage with Call
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There's nothing quite like inserting a quick lambda into a glom spec
to get the job done. But once a spec works, how can it be cleaned up?

.. autofunction:: glom.Call

Combining iterables with Flatten and friends
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*New in glom 19.1.0*

Got lists of lists? Sets of tuples? Or find yourself reaching for
Python's builtin :func:`sum` and :func:`reduce`? To handle these
situations, glom has three specifier types and one convenience
function:

.. autofunction:: glom.flatten

.. autoclass:: glom.Flatten

.. autoclass:: glom.Sum

.. autoclass:: glom.Fold

Object-oriented access and method calls with ``T``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

glom's shortest-named feature may be its most powerful.

.. autodata:: glom.T

.. _exceptions:

.. _check-specifier:

Validation with Check
^^^^^^^^^^^^^^^^^^^^^

Sometimes you want to confirm that your target data matches your
code's assumptions. With glom, you don't need a separate validation
step, you can do these checks inline with your glom spec, using
``Check``.

.. autoclass:: glom.Check

Exceptions
----------

glom introduces a few new exception types designed to maximize
readability and debuggability. Note that all these errors derive from
:exc:`GlomError`, and are only raised from :func:`glom()` calls, not
from spec construction or glom type registration. Those declarative
and setup operations raise :exc:`ValueError`, :exc:`TypeError`, and
other standard Python exceptions as appropriate.

.. autoclass:: glom.PathAccessError

.. autoclass:: glom.CoalesceError

.. autoclass:: glom.CheckError

.. autoclass:: glom.UnregisteredTarget

.. autoclass:: glom.PathAssignError

.. autoclass:: glom.GlomError

.. _debugging:

Debugging
---------

Even the most carefully-constructed specfications eventually need
debugging. If the error message isn't enough to fix your glom issues,
that's where **Inspect** comes in.

.. autoclass:: glom.Inspect

.. _setup-and-registration:

Setup and Registration
----------------------

For the vast majority of objects and types out there in Python-land,
:func:`~glom.glom()` will just work. However, for that very special
remainder, glom is ready and extensible!

.. autofunction:: glom.register
.. autoclass:: glom.Glommer
