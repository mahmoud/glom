``glom`` API reference
======================

.. automodule:: glom.core

The ``glom`` Function
---------------------

.. autofunction:: glom.glom


Advanced specification
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

.. autoclass:: glom.core.PathAccessError

.. autoclass:: glom.core.CoalesceError

.. autoclass:: glom.core.UnregisteredTarget

.. autoclass:: glom.core.GlomError

Debugging
---------

.. autoclass:: glom.Inspect
