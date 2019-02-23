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

    glom({1:2, 2:3}, Call(dict, args=(T.items(),)))
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

    glom([1, 2, 3], Call(deque, args=[T, 10]))
    glom([1, 2, 3], lambda t: deque(t, 10))


Filtered Iteration
------------------
Sometimes in addition to stepping through an iterable,
you'd like to omit some of the items from the result
set all together.  Here are two ways
to filter the odd numbers from a list.


.. code-block:: python

    glom([1, 2, 3, 4, 5, 6], lambda t: [i for i in t if i % 2])
    glom([1, 2, 3, 4, 5, 6], [lambda i: i if i % 2 else SKIP])


The second approach demonstrates the use of ``glom.SKIP`` to
back out of an execution.

This can also be combined with :class:`~glom.Coalesce` to
filter items which are missing sub-attributes.

Here is an example of extracting the primary email from a group
of contacts, skipping where the email is empty string, None,
or the attribute is missing.

.. code-block:: python

    glom(contacts, [Coalesce('primary_email.email', skip=('', None), default=SKIP)])


Preserve Type
-------------
The iteration specifier will walk lists and tuples.  In some cases it
would be convenient to preserve the target type in the result type.

This glomspec iterates over a tuple or list, adding one to each
element, and uses :class:`~glom.T` to return a tuple or list depending
on the target input's type.


.. code-block:: python

    glom((1, 2, 3), (
        {
            "type": type,
            "result": [lambda v: v + 1]  # arbitrary operation
        }, T['type'](T['result'])))


This demonstrates an advanced technique -- just as a tuple
can be used to process sub-specs "in series", a dict
can be used to store intermediate results while processing
sub-specs "in parallel" so they can then be recombined later on.


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


Filter Iterable
---------------

An iteration specifier can filter items out by using
:data:`~glom.SKIP` as the default of a :class:`~glom.Check` object.


.. code-block:: python

    glom(['cat', 1, 'dog', 2], [Check(types=str, default=SKIP)])
    # ['cat', 'dog']

You can also truncate the list at the first failing check by using
:data:`~glom.STOP`.

.. _lisp-style-if:

Lisp-style If Extension
-----------------------

Any class with a glomit method will be treated as a spec by glom.
As an example, here is a lisp-style If expression custom spec type:

.. code-block:: python

    class If(object):
        def __init__(self, cond, if_, else_=None):
            self.cond, self.if_, self.else_ = cond, if_, else_

        def glomit(self, target, scope):
            g = lambda spec: scope[glom](target, spec, scope)
            if g(self.cond):
                return g(self.if_)
            elif self.else_:
                return g(self.else_)
            else:
                return None

    glom(1, If(bool, {'yes': T}, {'no': T}))
    # {'yes': 1}
    glom(0, If(bool, {'yes': T}, {'no': T}))
    # {'no': 0}


Parellel Evaluation of Sub-Specs
--------------------------------

This is another example of a simple glom extension.
Sometimes it is convenient to execute multiple glom-specs
in parallel against a target, and get a sequence of their
results.

.. code-block:: python

    class Seq(object):
        def __init__(self, *subspecs):
            self.subspecs = subspecs

        def glomit(self, target, scope):
            return [scope[glom](target, spec, scope) for spec in self.subspecs]

    glom('1', Seq(float, int))
    # [1.0, 1]


Without this extension, the simplest way to achieve the same result is
with a dict:

.. code-block:: python

    glom('1', ({1: float, 2: int}, T.values()))
