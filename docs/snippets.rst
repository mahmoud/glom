Snippets
========

glom can do a lot of things, in the right hands. This doc makes those
hands yours, through sample code of useful building blocks and common
glom tasks.

.. contents:: Contents
   :local:

.. note::

   All samples below assume ``from glom import glom, T, Call`` and any
   other dependencies.

Reversing a Target
------------------
Here are a few ways to reverse the current target.


.. code-block:: python

    glom([1, 2, 3], T[::-1])
    glom([1, 2, 3], (reversed, list))



Iteration Result as Tuple
-------------------------
The glom iteration specifier returns a list;
it is easy to transform this however.


.. code-block:: python

    glom([1, 2, 3], ([T], tuple))


Data-Driven Dict Keys
---------------------
Glom's dict specifier interprets the dict keys
as constants.  A different technique is
required if the dict keys are part of the
target data rather than spec.


.. code-block:: python

    glom({1:2, 2:3}, Call(dict, args=T.items())
    glom({1:2, 2:3}, lambda t: dict(t.items()))
    glom({1:2, 2:3}, dict)


Construct Instance
------------------
A common use case is to construct an instance.
In the most basic case, the default behavior on
callable will suffice.


This converts a list of ints to a list of :class:`decimal.Decimal`
objects.


.. code-block:: python

    glom([1, 2, 3], [Decimal])


If additional arguments are required, :class:`~glom.Call` or ``lambda``
are good options.

This converts a list to a collection.deque,
while specifying a max size of 10.


.. code-block:: python

    glom([1, 2, 3], Call(deque, args=[T, 10])
    glom([1, 2, 3], lambda t: deque(t, 10))


Preserve Type
-------------
The iteration specifier will walk lists and tuples.
In some cases it would be convenient to preserve the
target type in the result type.

This glom will iterate over a tuple or
list, add one to each element, and return a tuple or
list depending on what it was passed.


.. code-block:: python

    glom((1, 2, 3), T.__class__([lambda v: v+1]))
