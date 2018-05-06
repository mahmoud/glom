``glom`` API reference
======================

.. automodule:: glom.core

.. contents::
   :local:

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

.. autoclass:: glom.Coalesce

.. autodata:: glom.OMIT


Reducing lambda usage with Call
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: glom.Call

Object-oriented access and method calls with ``T``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. attribute:: glom.T

   glom's shortest-named feature may be its most powerful.

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

.. autoclass:: glom.UnregisteredTarget

.. autoclass:: glom.GlomError

Debugging
---------

Even the most carefully-constructed specfications eventually need
debugging. If the error message isn't enough to fix your glom issues,
that's where **Inspect** comes in.

.. autoclass:: glom.Inspect

Registration and Setup
----------------------

For the vast majority of objects and types out there in Python-land,
:func:`~glom.glom()` will just work. However, for that very special
remainder, glom is ready and extensible!

.. autofunction:: glom.register
.. autoclass:: glom.Glommer
