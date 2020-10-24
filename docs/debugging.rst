Exceptions & Debugging
======================

While glom works well when all goes as intended, it even shines when
data doesn't match expectations. glom's error messages and exception
hierarchy have been designed to maximize readability and
debuggability. Read on for a listing of glom's exceptions and how to
debug them.

.. contents:: Contents
   :local:

.. _exceptions:

Exceptions
----------

glom introduces a several new exception types designed to maximize
readability and debuggability. Note that all these errors derive from
:exc:`GlomError`, and are only raised from :func:`glom()` calls, not
from spec construction or glom type registration. Those declarative
and setup operations raise :exc:`ValueError`, :exc:`TypeError`, and
other standard Python exceptions as appropriate.

Here is a short list of links to all public exception types in glom.

  .. hlist::
     :columns: 3

     * :exc:`~glom.GlomError`
     * :exc:`~glom.PathAccessError`
     * :exc:`~glom.PathAssignError`
     * :exc:`~glom.PathDeleteError`
     * :exc:`~glom.CoalesceError`
     * :exc:`~glom.FoldError`
     * :exc:`~glom.MatchError`
     * :exc:`~glom.TypeMatchError`
     * :exc:`~glom.CheckError`
     * :exc:`~glom.UnregisteredTarget`
     * :exc:`~glom.BadSpec`

.. _reading-exceptions:

Reading a glom Exception
------------------------

glom errors are regular Python exceptions, but may look a little
different from other Python errors. Because glom is a data
manipulation library, glom errors include a data traceback,
interleaving spec and target data.

For example, let's raise an error by glomming up some data that doesn't exist:

.. code-block:: default
   :linenos:

    >>> target = {'planets': [{'name': 'earth', 'moons': 1}]}
    >>> glom(target, ('planets', ['rings']))
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/mahmoud/projects/glom/glom/core.py", line 1787, in glom
        raise err
    glom.core.PathAccessError: error raised while processing, details below.
     Target-spec trace (most recent last):
     - Target: {'planets': [{'name': 'earth', 'moons': 1}]}
     - Spec: ('planets', ['rings'])
     - Spec: 'planets'
     - Target: [{'name': 'earth', 'moons': 1}]
     - Spec: ['rings']
     - Target: {'name': 'earth', 'moons': 1}
     - Spec: 'rings'
    glom.core.PathAccessError: could not access 'rings', part 0 of Path('rings'), got error: KeyError('rings')

Let's step through this output:


* Line **1**: We created a planet registry, similar to the one in the :doc:`tutorial`.
* Line **2-3**: We try to get a listing of ``rings`` of all the planets. Instead, we get a Python traceback.
* Line **7**: We see we have a :exc:`~glom.PathAccessError`.
* Line **8-9**: The "target-spec trace", our data stack, begins. It always starts with the target data as it was passed in.
* Line **10**: Next is the top-level spec, as passed in: ``('planets', ['rings'])``
* Line **11**: glom takes the first part of the spec from line 9, ``'planets'``, to get the next target.
* Line **12**: Because the spec on line 11 updated the current target, glom outputs it. When a spec is evaluated but the target value is unchanged, the target is skipped in the trace.
* Line **14-15**: We get to the last two lines, which include the culprit target and spec
* Line **16**: Finally, our familiar :exc:`~glom.PathAccessError` message,
  with more details about the error, including the original ``KeyError('rings')``.

This view of glom evaluation answers many of the questions
a developer or user would ask upon encountering the error:

* What was the data?
* Which part of the spec failed?
* What was the original error?

The data trace does this by peeling away at the target and spec until
it hones in on the failure. Both targets and specs in traces are
truncated to terminal width to maximize readability.

.. note::

   If for some reason you need the full Python stack instead of the
   glom data traceback, pass ``glom_debug=True`` to the top-level glom
   call.

.. _branched-exceptions:

Reading Branched Exceptions
---------------------------

Some glom spec types, like :class:`~glom.Coalesce` and
:class:`~glom.Switch`, can try multiple specs in succession. These
"branching" specs can also get multiple exceptions.

Initially, debugging data for these branching specs was limited. But
in v20.7.0, branching error trees were introduced, exposing
information about every spec and target attempted before raising the
final exception.

All the exception reading advice in the ":ref:`reading-exceptions`"
section applies, but there's a bit of extra formatting to visualize
the error tree in the target-spec trace.

Let's step line by line through a :class:`~glom.Coalesce` error tree:

.. code-block:: default
   :linenos:

    >>> target = {'n': 'nope', 'xxx': {'z': {'v': 0}}}
    >>> glom(target, Coalesce(('xxx', 'z', 'n'), 'yyy'))
    Traceback (most recent call last):
      File "tmp.py", line 9, in _make_stack
        glom(target, spec)
      File "/home/mahmoud/projects/glom/glom/core.py", line 2029, in glom
        raise err
    glom.core.CoalesceError: error raised while processing, details below.
     Target-spec trace (most recent last):
     - Target: {'n': 'nope', 'xxx': {'z': {'v': 0}}}
     + Spec: Coalesce(('xxx', 'z', 'n'), 'yyy')
     |\ Spec: ('xxx', 'z', 'n')
     || Spec: 'xxx'
     || Target: {'z': {'v': 0}}
     || Spec: 'z'
     || Target: {'v': 0}
     || Spec: 'n'
     |X glom.core.PathAccessError: could not access 'n', part 0 of Path('n'), got error: KeyError('n')
     |\ Spec: 'yyy'
     |X glom.core.PathAccessError: could not access 'yyy', part 0 of Path('yyy'), got error: KeyError('yyy')
    glom.core.CoalesceError: no valid values found. Tried (('xxx', 'z', 'n'), 'yyy') and got (PathAccessError, PathAccessError) (at path ['xxx', 'z'])

* Line **1-10**: Standard fare for glom use and error behavior, see ":ref:`reading-exceptions`"
* Line **11**: We see a "**+**" when starting a branching spec. Each level of branch adds a "**|**" on the left to help track nesting level.
* Line **12**: We see a "**\\**" indicating a new branch of the root branching spec.
* Line **13-17**: Traversing downward as usual until...
* Line **18**: We see an "**X**" indicating our first exception, causing the failure of this branch.
* Line **19**: We see a "**\\**" which starts our next branch.
* Line **20**: We see an "**X**" indicating our second and last exception, causing the failure of this branch.
* Line **21**: The last line is our root level exception, dedented, same as any other glom error.

Apart from the formatting, error branching doesn't change any other
semantics of the glom exception being raised.

.. _debugging:

Debugging
---------

Good error messages are great when the data has a problem, but what
about when a spec is incorrect?

Even the most carefully-constructed specifications eventually need
debugging. If the error message isn't enough to fix your glom issues,
that's where **Inspect** comes in.

.. autoclass:: glom.Inspect
