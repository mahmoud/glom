``glom`` by Analogy
===================

``glom`` is pure Python, and you don't need to know anything but
Python to use it effectively.

Still, most everyone who encounters ``glom`` for the first time finds
analogies to tools they already know. Whether SQL, list
comprehensions, or HTML templates, there seems to be no end to the
similarities. Many of them intentional!

While ``glom`` is none of those tools, and none of those tools are ``glom``, a
little comparison doesn't hurt. This document collects analogies to
help guide understanding along.


Similarity to list comprehensions
---------------------------------

One of the key inspirations for ``glom`` was the humble list
comprehension, one of my favorite Python features.

List comprehensions make your code look like its output, and that goes
a long way in readability. ``glom`` itself does list processing with
square brackets like ``[lambda x: x % 2]``, which actually makes it
more like a list comp and the old ``filter()`` function.

``glom``'s list processing differs in two ways:

* Required use of a callable or other ``glom`` spec, to enable deferred processing.
* Ability to return :data:`~glom.SKIP`, which can exclude items from a list.


Similarity to templating (Jinja, Django, Mustache)
--------------------------------------------------

``glom`` is a lot like templating engines, including modern formatters
like gofmt, but with all the format affordances distilled out. glom
doesn't just work on HTML, XML, JSON, or even just strings.

``glom`` works on objects, including functions, dicts, and all other
primitives. In fact, it would be safe to call ``glom`` an "object
templating" system.

A lot of insights for ``glom`` came (and continue to come) from writing ashes_.

.. _ashes: https://github.com/mahmoud/ashes


Similarity to SQL and GraphQL
-----------------------------

In some ways, ``glom`` is a Python query language for Python
objects. But thanks to its restructuring capabilities, it's much more
than SQL or GraphQL.

With SQL the primary abstraction is an table, or table-like
resultset. With GraphQL, the analogous answer to this is, of course,
the graph.

glom goes further, not only offering the Python object tree as a
graph, but also allowing you to change the shape of the data,
restructuring it while fetching and transforming values, which GraphQL
only minimally supports, and SQL barely supports at all. Table targets
get you table outputs.

Similiarity to validation (jsonschema, schema, cerberus)
--------------------------------------------------------

``glom`` is a generalized form of intake libraries `including validation`_.
We definitely took `schema`_
becoming successful as a sign that others shared our appetite for
succinct, declarative Python datastructure manipulation.

More importantly, these libraries seem to excel at structuring and
parsing data, and don't solve much on the other end. Translating
valid, structured objects like database models to JSON serializable
objects is glom's forté.

.. _schema: matching.rst
.. _including validation: https://github.com/mahmoud/glom/issues/7

Similarity to jq
----------------

:doc:`The CLI <cli>` that ``glom`` packs is very similar in function
to jq_, except it uses Python as its query language, instead of making
its own. Most importantly glom gives you `a programmatic way forward`_.

.. _jq: https://stedolan.github.io/jq/
.. _a programmatic way forward: http://sedimental.org/glom_restructured_data.html#library-first-then-cli

Similarity to XPath/XSLT
------------------------

These hallowed technologies of yore, they were way ahead of the game
in many ways. glom intentionally avoids their purity and verbosity,
while trying to take as much inspiration as possible from their
function.

Others
------

Beyond what's listed above, several other packages and language
features exist in glom's ballpark, including:

* `Specter (for Clojure) <https://github.com/nathanmarz/specter>`_
* `Lenses (for Haskell) <https://hackage.haskell.org/package/lens>`_
* `Dig (for Ruby Hashmaps) <https://ruby-doc.org/core-2.3.0_preview1/Hash.html#dig>`_

If you know of other useful comparisons, `let us know
<https://github.com/mahmoud/glom/issues/new>`_!
