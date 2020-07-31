Matching & Validation
=====================

.. automodule:: glom.matching

.. contents:: Contents
   :local:

Validation with Match
~~~~~~~~~~~~~~~~~~~~~

For matching whole data structures, use a :class:`~glom.Match` spec.

.. autoclass:: glom.Match
   :members:

Optional and required ``dict`` key matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note that our four :class:`~glom.Match` rules above imply that
:class:`object` is a match-anything pattern.  Because
``isinstance(val, object)`` is true for all values in Python,
``object`` is a useful stopping case. For instance, if we wanted to
extend an example above to allow additional keys and values in the
user dict above we could add :class:`object` as a generic pass through::

  >>> target = [{'id': 1, 'email': 'alice@example.com', 'extra': 'val'}]
  >>> spec = Match([{'id': int, 'email': str, object: object}]))
  >>> assert glom(target, spec) == \\
      ... [{'id': 1, 'email': 'alice@example.com', 'extra': 'val'}]
  True

The fact that ``{object: object}`` will match any dictionary exposes
the subtlety in :class:`~glom.Match` dictionary evaluation.

By default, value match keys are required, and other keys are
optional.  For example, ``'id'`` and ``'email'`` above are required
because they are matched via ``==``.  If either was not present, it
would raise class:`~glom.MatchError`.  class:`object` however is matched
with func:`isinstance()`. Since it is not an value-match comparison,
it is not required.

This default behavior can be modified with :class:`~glom.Required`
and :class:`~glom.Optional`.

.. autoclass:: glom.Optional

.. autoclass:: glom.Required

``M`` Expressions
~~~~~~~~~~~~~~~~~

The most concise way to express validation and guards.

.. autodata:: glom.M

Boolean operators and matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While ``M`` is an easy way to construct expressions, sometimes a more
object-oriented approach can be more suitable.

.. autoclass:: glom.Or

.. autoclass:: glom.And

.. autoclass:: glom.Not

String matching
~~~~~~~~~~~~~~~

.. autoclass:: glom.Regex

Control flow with ``Switch``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Match becomes even more powerful when combined with the ability to
branch spec execution.

.. autoclass:: glom.Switch

Exceptions
~~~~~~~~~~

.. autoclass:: glom.MatchError

.. autoclass:: glom.TypeMatchError

Validation with Check
~~~~~~~~~~~~~~~~~~~~~

.. warning::

   Given the suite of tools introduced with :class:`~glom.Match`, the
   :class:`Check` specifier type may be deprecated in a future
   release.

.. autoclass:: glom.Check

.. autoclass:: glom.CheckError
