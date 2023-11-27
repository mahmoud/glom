glom
====

*Restructuring data, the Python way.*

|release| |calver| |changelog|

**glom** is a new approach to working with data in Python, featuring:

* :ref:`Path-based access <access-granted>` for nested structures
* :ref:`Declarative data transformation <glom-func>` using lightweight, Pythonic specifications
* Readable, meaningful :ref:`error messages <exceptions>`
* Built-in :ref:`debugging <debugging>` features
* Plus, :doc:`deep assignment <mutation>`, :doc:`streaming <streaming>`, :doc:`data validation <matching>`, and *more*!

While it may sound like a lot, glom's straightforward approach becomes
second-nature very quickly. Start with the :doc:`tutorial<tutorial>`, 
or `try glom in your browser now`__!

.. __: https://yak.party/glompad/#spec=%22a.b.c%22%0A&target=%7B%22a%22%3A+%7B%22b%22%3A+%7B%22c%22%3A+%22d%22%7D%7D%7D%0A&v=1

Installation
------------

glom is pure Python, and tested on Python 3.7+, as well as
PyPy3. Installation is easy::

  pip install glom

Then you're ready to get glomming!

.. code-block:: python

   from glom import glom

   target = {'a': {'b': {'c': 'd'}}}
   glom(target, 'a.b.c')  # returns 'd'

There's much, much more to glom, check out the :doc:`tutorial` and :doc:`API reference<api>`!


*Just glom it! ☄️*


.. |release| image:: https://img.shields.io/pypi/v/glom.svg
             :target: https://pypi.org/project/glom/

.. |calver| image:: https://img.shields.io/badge/calver-YY.MM.MICRO-22bfda.svg
            :target: https://calver.org

.. |changelog| image:: https://img.shields.io/badge/CHANGELOG-UPDATED-b84ad6.svg
            :target: https://github.com/mahmoud/glom/blob/master/CHANGELOG.md


.. toctree::
   :maxdepth: 1
   :caption: Learning glom

   tutorial
   faq
   by_analogy
   snippets
   cli

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api
   mutation
   streaming
   grouping
   matching
   debugging

.. toctree::
   :maxdepth: 1
   :caption: Extending glom

   custom_spec_types
   modes
