``glom`` Command-Line Interface
===============================

.. note::

   glom's CLI is usable and useful, but keep in mind glom is a library *first*.


All the power of ``glom``, without even opening your text editor!

.. code-block:: text

   $ glom --help
   Usage: /home/mahmoud/bin/glom [FLAGS] [spec [target]]

   Command-line interface to the glom library, providing nested data
   access and data restructuring with the power of Python.

   Flags:

   --help / -h                     show this help message and exit
   --target-file TARGET_FILE       path to target data source (optional)
   --target-format TARGET_FORMAT
                                   format of the source data (json, python, toml,
                                   or yaml) (defaults to 'json')
   --spec-file SPEC_FILE           path to glom spec definition (optional)
   --spec-format SPEC_FORMAT       format of the glom spec definition (json, python,
                                     python-full) (defaults to 'python')
   --indent INDENT                 number of spaces to indent the result, 0 to disable
                                     pretty-printing (defaults to 2)
   --debug                         interactively debug any errors that come up
   --inspect                       interactively explore the data

The ``glom`` command will also read from standard input (stdin) and
process that data as the *target*.

Here's an example, filtering a GitHub API example to something much
more flat and readable:

.. code-block:: bash

   $ pip install glom
   $ curl -s https://api.github.com/repos/mahmoud/glom/events \
       | glom '[{"type": "type", "date": "created_at", "user": "actor.login"}]'

This yields:

.. code-block:: javascript

   [
     {
       "date": "2018-05-09T03:39:44Z",
       "type": "WatchEvent",
       "user": "asapzacy"
     },
     {
       "date": "2018-05-08T22:51:46Z",
       "type": "WatchEvent",
       "user": "CameronCairns"
     },
     {
       "date": "2018-05-08T03:27:27Z",
       "type": "PushEvent",
       "user": "mahmoud"
     },
     {
       "date": "2018-05-08T03:27:27Z",
       "type": "PullRequestEvent",
       "user": "mahmoud"
     }
     ...
   ]

By default the CLI *target* is JSON and the *spec* is a Python
literal.

.. note::

   Because the default CLI spec is a Python literal, there are no
   lambdas and other Python/glom constructs available. These features
   are gated behind the ``--spec-format python-full`` option to avoid
   code injection and other unwanted consequences.

The ``--debug`` and ``--inspect`` flags are useful for exploring
data. Note that they are not available when piping data through
stdin. Save that API response to a file and use ``--target-file`` to
do your interactive experimenting.
