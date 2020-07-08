Core ``glom`` API
=================

.. automodule:: glom.core

.. seealso::

   As the glom API grows, we've refactored the docs into separate
   domains. The core API is below. More specialized types can also be
   found in the following docs:

   .. hlist::
      :columns: 2

      * :doc:`mutation`
      * :doc:`streaming`
      * :doc:`grouping`
      * :doc:`matching`

   Longtime glom docs readers: thanks in advance for reporting/fixing
   any broken links you may find.

.. contents:: Contents
   :local:


.. _glom-func:

The ``glom`` Function
---------------------

Where it all happens. The reason for the season. The eponymous
function, :func:`~glom.glom`.

.. autofunction:: glom.glom

Basic Specifiers
----------------

Basic glom specifications consist of ``dict``, ``list``, ``tuple``,
``str``, and ``callable`` objects. However, as data calls for more
complicated interactions, ``glom`` provides specialized specifier
types that can be used with the basic set of Python builtins.


.. autoclass:: glom.Path
.. autoclass:: glom.Literal
.. autoclass:: glom.Spec

.. _advanced-specifiers:

.. seealso::

   Note that many of the Specifier types previously mentioned here
   have moved into their own docs, among them:

   .. hlist::
      :columns: 2

      * :doc:`mutation`
      * :doc:`streaming`
      * :doc:`grouping`
      * :doc:`matching`

Object-Oriented Access and Method Calls with T
----------------------------------------------

glom's shortest-named feature may be its most powerful.

.. autodata:: glom.T


Defaults with Coalesce
----------------------

Data isn't always where or what you want it to be. Use these
specifiers to declare away overly branchy procedural code.

.. autoclass:: glom.Coalesce

.. autodata:: glom.SKIP
.. autodata:: glom.STOP


Calling Callables with Invoke
-----------------------------

.. versionadded:: 19.10.0

From calling functions to constructing objects, it's hardly Python if
you're not invoking callables. By default, single-argument functions
work great on their own in glom specs. The function gets passed the
target and it just works:

>>> glom(['1', '3', '5'], [int])
[1, 3, 5]

Zero-argument and multi-argument functions get a lot trickier,
especially when more than one of those arguments comes from the
target, thus the :class:`Invoke` spec.

.. autoclass:: glom.Invoke
   :members:

Alternative approach to functions: Call
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An earlier, more primitive approach to callables in glom was the Call
specifier type.

.. warning::

   Given superiority of its successor, :class:`Invoke`,
   the :class:`Call` type may be deprecated in a future release.

.. autoclass:: glom.Call


Self-Referential Specs
----------------------

Sometimes nested data repeats itself, either recursive structure or
just through redundancy.

.. autoclass:: glom.Ref

Core Exceptions
---------------

Not all data is going to match specifications. Luckily, glom errors
are designed to be as readable and actionable as possible.

All glom exceptions inherit from :exc:`GlomError`, described below,
along with other core exception types. For more details about handling
and debugging exceptions, see ":doc:`debugging`".

.. autoclass:: glom.PathAccessError

.. autoclass:: glom.CoalesceError

.. autoclass:: glom.UnregisteredTarget

.. autoclass:: glom.BadSpec

.. autoclass:: glom.GlomError


.. _setup-and-registration:

Setup and Registration
----------------------

When it comes to targets, :func:`~glom.glom()` will operate on the
vast majority of objects out there in Python-land. However, for that
very special remainder, glom is readily extensible!

.. autofunction:: glom.register
.. autoclass:: glom.Glommer
