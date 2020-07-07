Exceptions and Debugging
========================

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

.. _debugging:


Debugging
---------

Good error messages are great when the data has a problem, but what
about when a spec is incorrect?

Even the most carefully-constructed specifications eventually need
debugging. If the error message isn't enough to fix your glom issues,
that's where **Inspect** comes in.

.. autoclass:: glom.Inspect
