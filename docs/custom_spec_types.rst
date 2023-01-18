Writing a custom Specifier Type
===============================

While glom comes with a lot of built-in features, no library can ever
encompass all data manipulation operations.

To cover every case out there, glom provides a way to extend its
functionality with your own data handling hooks. This document
explains glom's execution model and how to integrate with it when
writing a custom Specifier Type.

When to write a Specifier Type
------------------------------

``glom`` has always supported arbitrary callables, like so:

.. code::

   glom({'nums': range(5)}, ('nums', sum))
   # 10

With this built-in extensibility, what does a glom specifier type add?

Custom specifier types are useful when you want to:

  1. Perform validation at spec construction time
  2. Enable users to interact with new target types and operations
  3. Improve readability and reusability of your data transformations
  4. Temporarily change the glom runtime behavior

If you're just building a one-off spec for transforming your own data,
there's no reason to reach for an extension. ``glom``'s extension API
is easy, but a good old Python ``lambda`` is even easier.

Building your Specifier Type
----------------------------

Any object instance with a ``glomit`` method can participate in a glom
call. By way of example, here is a programming cliché implemented as a
glom specifier type, with comments referencing notes below.

.. code::

 class HelloWorldSpec(object):  # 1
     def glomit(self, target, scope):  # 2
         print("Hello, world!")
         return target

And now let's put it to use!

.. code::

  from glom import glom

  target = {'example': 'object'}

  glom(target, HelloWorldSpec())  # 3
  # prints "Hello, world!" and returns target

There are a few things to note from this example:

  1. Specifier types do not need to inherit from any type. Just
     implement the ``glomit`` method.
  2. The ``glomit`` signature takes two parameters, ``target`` and
     ``scope``. The ``target`` should be familiar from using
     :func:`~glom.glom`, and it's the ``scope`` that makes glom really
     tick.
  3. By convention, instances are used in specs passed to
     :func:`~glom.glom` calls, not the types themselves.

.. _glom_scope:

The glom Scope
--------------

The :ref:`glom scope<scope>` is also used to expose runtime state to the specifier
type. Let's take a look inside a scope:

.. code::

 from glom import glom
 from pprint import pprint

 class ScopeInspectorSpec(object):
     def glomit(self, target, scope):
         pprint(dict(scope))
         return target

 glom(target, ScopeInspectorSpec())

Which gives us:

.. code::

   {T: {'example': 'object'},
   <function glom at 0x7f208984d140>: <function _glom at 0x7f208984d5f0>,
   <class 'glom.core.Path'>: [],
   <class 'glom.core.Spec'>: <__main__.ScopeInspectorSpec object at 0x7f208bf58690>,
   <class 'glom.core.Inspect'>: None,
   <class 'glom.core.TargetRegistry'>: <glom.core.TargetRegistry object at 0x7f208984b4d0>}

As you can see, all glom's core workings are present, all under familiar keys:

  * The current *target*, accessible using :data:`~glom.T` as a scope key.
  * The current *spec*, accessible under :class:`~glom.Spec`.
  * The current *path*, accessible under :class:`~glom.Path`.
  * The ``TargetRegistry``, used to :ref:`register new operations and target types <setup-and-registration>`.
  * Even the ``glom()`` function itself, filed under :func:`~glom.glom`.

To learn how to use the scope's powerful features idiomatically, let's
reimplement at one of glom's standard specifier types.

Specifiers by example
---------------------

While we've technically created a couple of extensions above, let's
really dig into the features of the scope using an example.

:class:`~glom.Sum` is a standard extension that ships with glom, and
it works like this:

.. code::

   from glom import glom, Sum

   glom([1, 2, 3], Sum())
   # 6

The version below does not have as much error handling, but reproduces
all the same basic principles. This version of ``Sum()`` code also
contains comments with references to explanatory notes below.

.. code::

 from glom import glom, Path, T
 from glom.core import TargetRegistry, UnregisteredTarget  # 1

 class Sum(object):
    def __init__(self, subspec=T, init=int):  # 2
        self.subspec = subspec
        self.init = init

    def glomit(self, target, scope):
        if self.subspec is not T:
            target = scope[glom](target, self.subspec, scope)  # 3

        try:
            # 4
            iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])
        except UnregisteredTarget as ut:
            # 5
            raise TypeError('can only %s on iterable targets, not %s type (%s)'
                            % (self.__class__.__name__, type(target).__name__, ut))

        try:
            iterator = iterate(target)
        except Exception as e:
            raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                            % (target.__class__.__name__, Path(*scope[Path]), e))

        return self._sum(iterator)

    def _sum(self, iterator):  # 6
        ret = self.init()

        for v in iterator:
            ret += v

        return ret

Now, let's take a look at the interesting parts, referencing the comments above:

  1. Specifier types often reference the :class:`TargetRegistry`,
     which is not part of the top-level ``glom`` API, and must be
     imported from ``glom.core``. More on this in #4.
  2. Specifier type ``__init__`` methods may take as many or as few
     arguments as desired, but many glom specifier types take a first
     parameter of a *subspec*, meant to be fetched right before the
     actual specifier's operation. This helps readability of
     glomspecs. See :class:`~glom.Coalesce` for an example of this
     idiom.
  3. Specifier types should not reference the
     :func:`~glom.glom()` function directly, instead use the
     :func:`~glom.glom` function as a key to the ``scope`` map to get the
     currently active ``glom()``. This ensures that the extension type is
     compatible with advanced specifier types which override the
     ``glom()`` function.
  4. To maximize compatiblity with new target types, ``glom`` allows
     :ref:`new types and operations to be registered
     <setup-and-registration>` with the ``TargetRegistry``. Specifier types
     should respect this by contextually fetching these standard
     operators as demonstrated above. At the time of writing, the
     primary operators used by glom itself are ``"get"``,
     ``"iterate"``, ``"keys"``, ``"assign"``, and ``"delete"``.
  5. In the event that the current target does not support your
     Specifier type's desired operation, it's customary to raise a helpful
     error. Consider creating your own exception type and inheriting
     from :class:`~glom.GlomError`.
  6. Specifier types may have other methods and members in addition to
     the primary ``glomit()`` method. This ``_sum()`` method
     implements most of the core of our custom specifier type.

Check out the implementation of the real :class:`glom.Sum()` specifier for more details.

Summing up
----------

``glom`` Specifier Types are more than just add-ons; the extension
architecture is how most of ``glom`` itself is implemented. Build
knowing that the paradigm is as powerful as anything built-in.

If you need more examples, another simple one can be found in
:ref:`this snippet <lisp-style-if>`. ``glom``'s source code itself
contains many specifiers more advanced than the above. Simply search
the codebase for ``glomit()`` methods and you will find no shortage.

Happy extending!
