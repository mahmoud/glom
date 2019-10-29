glom's CHANGELOG
================

glom is a growing library! This document is a record of its growth.

The glom team's approach to updates can be summed up as:

* Always maintaining backwards compatibility
* [CalVer](https://calver.org) versioning scheme (`YY.MM.MICRO`)
* Stay streamlined. glom should be a well-designed bicycle, not an
  aircraft carrier.

Check this page when upgrading, we strive to keep the updates
summarized and well-linked.

19.10.0
-------
*(October 29, 2019)*

* Add streaming support via [Iter][iter] ([#100][i100])
* Add better callable handling with [Invoke][invoke] ([#101][i101])
* Add Fill ([#110][i110]) - Also adds Auto for the default mode. (soft-launch, docs TBA)
* Add Let for variable capture ([#108][i108]) (soft-launch, docs TBA)
* Steps in the tuple now nest scopes ([#97][i97])
* All public specifier types now have reasonable reprs (notably, Coalesce, Check, and Assign)

[iter]: https://glom.readthedocs.io/en/latest/api.html#glom.Iter
[invoke]: https://glom.readthedocs.io/en/latest/api.html#glom.Invoke
[i97]: https://github.com/mahmoud/glom/issues/97
[i100]: https://github.com/mahmoud/glom/issues/100
[i101]: https://github.com/mahmoud/glom/issues/101
[i108]: https://github.com/mahmoud/glom/issues/108
[i110]: https://github.com/mahmoud/glom/issues/110

19.2.0
------
*(February 17, 2019)*

Add [`Merge()` spec and `merge()` convenience
function](https://glom.readthedocs.io/en/latest/api.html#glom.merge),
for turning iterables of mappings into a single mapping.

Additionally, `T` and `Spec()` instances which appear in the "key"
portion of the default dict/mapping spec, are now evaluated, enabling
operations [like this](https://github.com/mahmoud/glom/issues/85),
which demonstrates both new features:

```python

from glom import glom, T, Merge

target = [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]
spec = Merge([{T["id"]: T["name"]}])

glom(target, spec)
# {1: 'foo', 2: 'bar'}
```

19.1.0
------
*(January 20, 2019)*

Added features related to folding/reducing sequences. Read more about
`Fold`, `Sum`, `Flatten`, and `flatten`
[here](https://glom.readthedocs.io/en/latest/api.html#combining-iterables-with-flatten-and-friends).

Also switched CalVer version scheme to `YY.MM.MICRO`.

18.4.0
------
*(December 25, 2018)*

A couple features related to
[`assign()`](https://glom.readthedocs.io/en/latest/api.html#glom.assign)
and other minor additions and fixes.

* Add new `missing` parameter to `assign()`, to autogenerate new
  datastructures at paths that don't exist. Read more at the bottom of
  the [`Assign` spec docstring](https://glom.readthedocs.io/en/latest/api.html#glom.Assign).
* Allow `Assign` to operate on `S`-based specs to assign to the spec.
* Add the [`STOP` singleton](https://glom.readthedocs.io/en/latest/api.html#glom.STOP).
  `STOP` is to [`SKIP`](https://glom.readthedocs.io/en/latest/api.html#glom.SKIP)
  what `break` is to `continue`. Useful as a default with conditional specs like
  [`Check()`](https://glom.readthedocs.io/en/latest/api.html#validation-with-check).

18.3.1
------

*(August 22, 2018)*

Fix a small bug where `Assign()` raised a `TypeError` instead of a
`GlomError` subtype. This release added
[`PathAssignError`](https://glom.readthedocs.io/en/latest/api.html#glom.PathAssignError),
which is now raised instead.

18.3.0
------
*(August 14, 2018)*

This release introduces the `Assign` Spec type, and its accompanying
`glom.assign()` "deep-set" convenience function, a feature that
required the refinement of glom's Extension API. `Path` and `T` also
saw improvements.

* `Assign` Spec type and `glom.assign()` top-level function for deep setting.
* Extensions (and advanced users) can now register new operations. For
  instance, `Assign` registers `"assign"`, which is now a peer of
  `"get"` and `"iterate"`, which were the only built-in operations
  glom provided.
* Extensions no longer need to be registered. A `glom` extension is an
  instance of any type that provides a `glomit()` method. Full docs
  coming soon.
* `T` and other `TType` instances now pickle correctly, fixing [#48][i48]
* `Path` instances now behave like strings, with indexing returning
  new `Path` objects, with full slice syntax support.
* `Path` also supports `.values()` and `.items()` methods, which
  enable getting sequences of the data backing the `Path()`, for when
  a sub-`Path` object is not desirable.
* `Path` objects are now comparable for equality. To compare a `T`,
  simply wrap it in a `Path()` use the `==` operator.

[i48]: https://github.com/mahmoud/glom/issues/48

18.2.0
------
*(July 5, 2018)*

This sizable release incorporates a lot of the post-announcement
feedback. Several advanced features were added, including an extension
API and "Scope" support. While this involved a large refactor, all
external APIs are 100% backwards-compatible.

In other good news, coverage is up over 90% and on track to go even
higher. Check out all the well-tested enhancements below!

* Introduce the `glom`'s first-class Extension system. Docs are a work
  in progress, but given that all the internals are implemented in
  terms of the system, don't hesitate to look under the hood and start
  experimenting. Addresses [#9][i9].
* The Extension system involved a runtime refactor to add a concept of
  "scope" to `glom`. Until now, glom has only supported operating on a
  single "target", making it the only object in scope. Now, it's also
  possible to add other objects to the scope, making multi-target
  glomming a reality for advanced users.
* Add initial version of `Check()`, a specifier type aimed at
  providing target validation while glomming. Addresses [#7][i7].
* Make `Spec` work for object-oriented glom use. Usage is similar to
  Python's `re.compile`: predefine a `Spec` object, call
  `spec.glom(target)` later. Addresses [#14][i14]
* Add YAML support to CLI. PyYAML was added as an "extras" dependency
  and is not installed by default. glom will pick up any existing
  installed yaml library and use that, or you can `pip install
  glom[yaml]` to explicitly install support. See [#26][i26] for
  details. Thanks @dfezzie!
* Made `T` and `Path` share evaluation, repr, and exception paths, closing [#6][i6]
* add `default_factory` argument to Coalesce, with semantics identical
  to Python's built-in defaultdict.

[i6]: https://github.com/mahmoud/glom/issues/6
[i7]: https://github.com/mahmoud/glom/issues/7
[i9]: https://github.com/mahmoud/glom/issues/9
[i14]: https://github.com/mahmoud/glom/issues/14
[i26]: https://github.com/mahmoud/glom/issues/26

18.1.1
------
*(May 9, 2018)*

Initial release.

See the [announcement post][initial_announce] for an idea of the
functionality available.

This release itself added the console interface (CLI).

18.1.0
------
*(May 6, 2018)*

Still in semi-public beta. This release added `T` objects and better
error messages.


18.0.0
------
*(April 30, 2018)*

Semi-public beta release. Most of the functionality glom had on
[announcement][initial_announce].

[initial_announce]: https://sedimental.org/glom_restructured_data.html

0.0.1
-----
*(April 18, 2018)*

Barely more than a function definition. For the historically-oriented,
here's a [blast from the
past](https://github.com/mahmoud/glom/blob/186757b47af3d33901df4bf715874b5f3c781d8f/glom/__init__.py#L74-L91),
representing the core of glom functionality.
