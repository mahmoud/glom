glom
====

*Declarative object access and templating*

|release| |calver|

**glom** is a new approach to working with data in Python.

.. |release| image:: https://img.shields.io/pypi/v/boltons.svg
             :target: https://pypi.python.org/pypi/boltons

.. |calver| image:: https://img.shields.io/badge/calver-YY.MINOR.MICRO-22bfda.svg
            :target: https://calver.org


.. toctree::
   :maxdepth: 2

   tutorial
   api
   cli

Installation and Integration
----------------------------

glom is pure Python, and tested on Python 2.7-3.7, as well as
PyPy. Installation is easy::

  pip install glom

Then you're ready to get glomming!::

  from  glom import glom

  target = {'a': {'b': {'c': 'd'}}}
  glom(target, 'a.b.c')  # returns 'd'

There's much, much more to glom, check out the tutorial and API reference!


*Just glom it! ☄️*
