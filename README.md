# glom

*glom gets results, conglomeratively.*

Real applications have real data, and real data nests. Objects inside
of objects inside of lists of objects.

glom is a powerful and declarative way to handle real-world nested
data. A sort of *object templating*.

## Introduction

Think back, probably not too far, to a time you saw code like this:

```python
value = target.a['b']['c']
```

This code probably gives you back the value you want. But experienced
developers know how fragile it can be. This tiny line can raise any of
the following:

```
AttributeError: 'TargetType' object has no attribute 'a'
KeyError: 'b'
TypeError: 'NoneType' object has no attribute '__getitem__'
TypeError: list indices must be integers, not str
```

And for those last two, where in the line did the failure occur? `a`
or `a['b']` or `a['b']['c']`?

Experienced developers will often split this code up to be more
debuggable, but this leads to verbose, tedious code, with its own set
of maintenance issues.

Enter glom.

glom is a new, Pythonic approach to nested data that makes all these
problems go away.

```python
value = glom(target, 'a.b.c')
```

On success, you get your value, same as ever. On failure, you see:

```
PathAccessError: could not access 'c' from path Path('a', 'b', 'c'), got error: ...
```

And that's just the beginning.

## Object templating

glom goes far beyond deep access, implementing a coherent, declarative
approach for accessing and building objects. glom's envisions the
ideal data manipulation as code resembling the data itself.

For instance, if requirements change, and `target` becomes a list, our
access code becomes:

```python
value = glom(target, ['a.b.c'])
```

If we want a more full-fledged object wrapping for our results:

```python
value = glom(target, {'result_count': len,
                      'results': [{'c': 'a.b.c'}]})
```

glom not only calls callables (`len`), it supports chained calls with
tuples, fallback calls with `Coalesce`, and interactive debugging with
`Inspect`. See [the tutorial](https://github.com/mahmoud/glom/blob/master/glom/tutorial.py)
and API reference for more in-depth docs.

## FAQ

Paradigm shifts always raise a question or two.

### *What does "glom" mean?*

"glom" is short for "conglomerate", and can be used as a noun or
verb. An astronomer might say, "space dust gloms together to create
planets and planetoids". Got some data you need to transform? Glom it!

### Any other handy terminology?

A couple of terms that help navigate around glom's powerful semantics:

* **target** - Glom operates on a variety of inputs, so we simply
  refer to the object being accessed as the "target"
* **spec** - *(aka "glomspec")* The accompanying template used to
  specify the structure of the returned value.

### Other tips?

Just a few (for now):

* Specs don't have to live in the glom call. You can put them
  anywhere. Commonly-used specs work as class attributes and globals.
* Using glom's declarative approach does wonders for code coverage,
  much like [attrs](https://github.com/python-attrs/attrs) and
  [schema](https://github.com/keleshev/schema), both of which go great
  with glom.
* Advanced tips
    * glom is designed to support all of Python's built-ins as targets,
      and is readily extensible to other types, through glom's
      `register()` call.
    * If you're trying to minimize global state, consider
      instantiating your own `glom.Glommer` object to encapsulate any
      type registration changes.

## TODO

* Expand tutorial
* API docs
