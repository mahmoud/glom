Examples & Snippets
===================

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
            "result": [T + 1]  # arbitrary operation
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

    glom(['cat', 1, 'dog', 2], [Check(type=str, default=SKIP)])
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


Clamp Values
------------

A common numerical operation is to clamp values -- if they
are above or below a certain value, assign them to that value.

Using a pattern-matching glom idiom, this can be implemented
simply:

.. code-block:: python

    glom(range(10), [(M < 7) | Val(7)])
    # [0, 1, 2, 3, 4, 5, 6, 7, 7, 7]


What if you want to drop rather than clamp out-of-range values?

.. code-block:: python

    glom(range(10), [(M < 7) | Val(SKIP)])
    # [0, 1, 2, 3, 4, 5, 6]


Transform Tree
--------------

With an arbitrary depth tree, :class:`~glom.Ref` can be used to
express a recursive spec.

For example, this `etree2dicts` spec will recursively walk an `ElementTree`
instance and transform it from nested objects to nested dicts.

.. code-block:: python

    etree2dicts = Ref('ElementTree',
        {"tag": "tag", "text": "text", "attrib": "attrib", "children": (iter, [Ref('ElementTree')])})


Alternatively, say we only wanted to generate tuples of tag and children:

.. code-block:: python

    etree2tuples = Fill(Ref('ElementTree', (T.tag, Iter(Ref('ElementTree')).all())))


(Note also the use of :class:`~glom.Fill` mode to easily construct a tuple.)

.. code-block:: html

    <html>
      <head>
        <title>the title</title>
      </head>
      <body id="the-body">
        <p>A paragraph</p>
      </body>
    </html>


Will translate to the following tuples:

.. code-block:: python

    >>> etree = ElementTree.fromstring(html_text)
    >>> glom(etree, etree2tuples)
    ('html', [('head', [('title', [])]), ('body', [('p', [])])])


Fix Up Strings in Parsed JSON
-----------------------------

Tree-walking with :class:`~glom.Ref()` combines powerfully with
pattern matching from :class:`~glom.Match()`.

In this case, consider that we want to transform parsed JSON recursively,
such that all unicodes are converted to native strings.


.. code-block:: python

    glom(json.loads(data),
        Ref('json',
            Match(Switch({
                dict: {Ref('json'): Ref('json')},
                list: [Ref('json')],
                type(u''): Auto(str),
                object: T}))
            )
        )


:class:`~glom.Match()` above splits the :class:`~glom.Ref()` evaluation into 4 cases:

* on :class:`dict`, use :class:`~glom.Ref()` to recurse for all keys and values
* on :class:`list`, use :class:`~glom.Ref()` to recurse on each item
* on text objects (``type(u'')``) -- py3 :class:`str` or py2
  :class:`unicode` -- transform the target with :class:`str`
* for all other values (``object``), pass them through

As motivation for why this might come up: attributes, class names,
function names, and identifiers must be the native string type for a
given Python, i.e., bytestrings in Python 2 and unicode in Python 3.


Store and Retrieve Current Target
---------------------------------

The :data:`~glom.A` scope assignment helper makes it 
convenient to hold on to the current target and then reset it.

The ``(A.t, ..., S.t)`` "sandwich" is a convenient idiom for these
cases.

For example, we could use this to update a ``dict``:


.. code-block:: python

    glom({}, (A.t, T.update({1: 1}), S.t))


Accessing Ancestry
------------------

The technique above can be useful when you want to flatten an object structure by combining child, 
parent, and/or grandparent data. For instance:

.. code-block:: python

    input_data = {"a": {"b": {"c": 1}}}
    # transform to:
    output_data = [{"value": 1, "grandparent": "a"}]

We can do this by leveraging glom's Scopes_. Here's the spec to get the results above:

.. code-block:: python

    (
        T.items(),
        [
            (
                A.globals.gp_item,  # save the grandparent item to the global scope
                T[1].values(),      # access the values as usual
                [{"value": "c", "grandparent": S.globals.gp_item[0]}],  # access the grandparent item
            )
        ],
        Flatten(),
    )

You can play with glom scopes `in your browser here`__.

.. __: https://yak.party/glompad/#spec=%28%0A++++T.items%28%29%2C%0A++++%5B%28%0A++++++++++++A.globals.gp_item%2C%0A++++++++++++T%5B1%5D.values%28%29%2C%0A++++++++++++%5B%7B%22val%22%3A+%22c%22%2C+%22path%22%3A+S.globals.gp_item%5B0%5D%7D%5D%2C%0A++++%29%5D%2C%0A++++Flatten%28%29%2C%0A%29%0A&target=%7B%0A++%22a%22%3A+%7B%0A++++%22b%22%3A+%7B%0A++++++%22c%22%3A+1%0A++++%7D%0A++%7D%0A%7D&v=1

.. _Scopes: https://glom.readthedocs.io/en/latest/api.html#updating-the-scope-s-a

Note that at the time of writing, glom doesn't yet have full tree traversal, so the nesting of 
the spec is going to roughly match the nesting of your data. If you need this to work in an 
arbitrarily nested structure, we recommend `remap <https://sedimental.org/remap.html>`_, 
the recursive map function.