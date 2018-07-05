glom's CHANGELOG
================

glom is a growing library! This document is a record of its growth.

The glom team's approach to updates can be summed up as:

* Always maintaining backwards compatibility
* [CalVer](https://calver.org) versioning scheme (`YY.MINOR.MICRO`)
* Stay streamlined. glom should be a well-designed bicycle, not an
  aircraft carrier.

Check this page when upgrading, we strive to keep the updates
summarized and well-linked.

18.1.0
------
*(July 5, 2018)*

A sizable release, incorporating a lot of the post-announcement
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

18.0.0
------
*(May 9, 2018)*

Initial release.

See the [announcement
post](https://sedimental.org/glom_restructured_data.html) for an idea
of the functionality available.
