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

Here are a couple ways to reverse the current target. The first uses
basic Python builtins, the second uses the :data:`~glom.T` object.


.. code-block:: python

    glom([1, 2, 3], (reversed, list))
    glom([1, 2, 3], T[::-1])


Iteration Result as Tuple
-------------------------

The default glom iteration specifier returns a list, but it's easy to
turn that list into a tuple. The following returns a tuple of
absolute-valued integers:


.. code-block:: python

    glom([-1, 2, -3], ([abs], tuple))


Data-Driven Assignment
----------------------

glom's dict specifier interprets the keys as constants.  A different
technique is required if the dict keys are part of the target data
rather than spec.


.. code-block:: python

    glom({1:2, 2:3}, Call(dict, args=T.items())
    glom({1:2, 2:3}, lambda t: dict(t.items()))
    glom({1:2, 2:3}, dict)


Construct Instance
------------------

A common use case is to construct an instance.  In the most basic
case, the default behavior on callable will suffice.


The following converts a list of ints to a list of
:class:`decimal.Decimal` objects.


.. code-block:: python

    glom([1, 2, 3], [Decimal])


If additional arguments are required, :class:`~glom.Call` or ``lambda``
are good options.

This converts a list to a collection.deque,
while specifying a max size of 10.


.. code-block:: python

    glom([1, 2, 3], Call(deque, args=[T, 10])
    glom([1, 2, 3], lambda t: deque(t, 10))


Preserve Target Type
--------------------

The iteration specifier will walk lists and tuples.  In some cases it
would be convenient to preserve the target type in the result type.

This glomspec iterates over a tuple or list, adding one to each
element, and uses :class:`~glom.T` to return a tuple or list depending
on the target input's type.


.. code-block:: python

    glom((1, 2, 3), T.__class__([lambda v: v + 1]))


Automatic Django ORM type handling
----------------------------------

In day-to-day Django ORM usage, Managers_ and QuerySets_ are
everywhere. They work great with glom, too, but they work even better
when you don't have to call ``.all()`` all the time. Enable automatic
iteration using the following :meth:`~glom.register` technique:

.. code-block:: python

    import glom
    import django.db.models

    glom.register(django.db.models.Manager, iterate=lambda m: m.all())
    glom.register(django.db.models.QuerySet, iterate=lambda qs: qs.all())

Call this in ``settings`` or somewhere similarly early in your
application setup for the best results.

.. _Managers: https://docs.djangoproject.com/en/2.0/topics/db/managers/
.. _QuerySets: https://docs.djangoproject.com/en/2.0/ref/models/querysets/
