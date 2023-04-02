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
.. autoclass:: glom.Val
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

.. _scope:

The ``glom`` Scope
------------------

Sometimes data transformation involves more than a single target and
spec. For those times, glom has a *scope* system designed to manage
additional state.

Basic usage
~~~~~~~~~~~

On its surface, the glom scope is a dictionary of extra values that
can be passed in to the top-level glom call. These values can then be
addressed with the **S** object, which behaves
similarly to the :data:`~glom.T` object.

Here's an example case, counting the occurrences of a value in the
target, using the scope:

  >>> count_spec = T.count(S.search)
  >>> glom(['a', 'c', 'a', 'b'], count_spec, scope={'search': 'a'})
  2

Note how **S** supports attribute-style dot-access for its keys. For
keys which are not valid attribute names, key-style access is also
supported.

.. note::

   glom itself uses certain keys in the scope to manage internal
   state. Consider the namespace of strings, integers, builtin types,
   and other common Python objects open for your usage.  Read
   :doc:`the custom spec doc<custom_spec_types>` to learn about more
   advanced, reserved cases.

Updating the scope - ``S()`` & ``A``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

glom's scope isn't only set once when the top-level :func:`glom`
function is called. It's dynamic and updatable.

If your use case requires saving a value from one part of the target
for usage elsewhere, then **S** will allow you to save values
to the scope::

    >>> target = {'data': {'val': 9}}
    >>> spec = (S(value=T['data']['val']), {'val': S['value']})
    >>> glom(target, spec)
    {'val': 9}

Any keyword arguments to the **S** will have their values evaluated as
a spec, with the result being saved to the keyword argument name in
the scope.

When only the target is being assigned, you can use the **A** as a
shortcut::

    >>> target = {'data': {'val': 9}}
    >>> spec = ('data.val', A.value, {'val': S.value})
    >>> glom(target, spec)
    {'val': 9}

**A** enables a shorthand which assigns the current target to a
location in the scope.


Sensible saving - ``Vars`` & ``S.globals``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Of course, glom's scopes do not last forever. Much like function calls
in Python, new child scopes can see and read values in parent
scopes. When a child spec saves a new value to the scope, it's lost
when the child spec completes.

If you need values to be saved beyond a spec's local scope, the best
way to do that is to create a :class:`~glom.Vars` object in a common
ancestor scope. :class:`~glom.Vars` acts as a mutable namespace where
child scopes can store state and have it persist beyond their local
scope. Choose a location in the spec such that all involved child
scopes can see and share the value.

  .. note::

     glom precreates a *global* :class:`~glom.Vars` object at
     ``S.globals``. Any values saved there will be accessible
     throughout that given :func:`~glom.glom` call::

       >>> last_spec = ([A.globals.last], S.globals.last)
       >>> glom([3, 1, 4, 1, 5], last_spec)
       5

     While not shared across calls, most of the same care prescribed
     about using global state still applies.

.. autoclass:: glom.Vars


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
.. autofunction:: glom.register_op
.. autoclass:: glom.Glommer
