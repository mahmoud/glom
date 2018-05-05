``glom`` API reference
======================

.. automodule:: glom.core

The ``glom`` Function
---------------------

Where it all happens. The reason for the season. The eponymous function, ``glom``.

.. autofunction:: glom.glom


Advanced Specification
----------------------

.. autoclass:: glom.Path
.. autoclass:: glom.Literal
.. autoclass:: glom.Coalesce

Registration and Setup
----------------------

.. autoclass:: glom.register
.. autoclass:: glom.Glommer

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
