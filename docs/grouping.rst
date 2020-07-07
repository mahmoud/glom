Reduction & Grouping
====================

This document contains glom techniques for transforming a collection
of data to a smaller set, otherwise known as "grouping" or
"reduction".

Combining iterables with Flatten and Merge
------------------------------------------

.. versionadded:: 19.1.0

Got lists of lists? Sets of tuples? A sequence of dicts (but only want
one)? Do you find yourself reaching for Python's builtin :func:`sum`
and :func:`reduce`? To handle these situations and more, glom has five
specifier types and two convenience functions:

.. autofunction:: glom.flatten

.. autoclass:: glom.Flatten

.. autofunction:: glom.merge

.. autoclass:: glom.Merge

.. autoclass:: glom.Sum

.. autoclass:: glom.Fold

Exceptions
----------

.. autoclass:: glom.FoldError
