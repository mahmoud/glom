"""
Helpers for streaming use cases -- that is, glom-specs which yield their
results one part at a time so that they can be applied to targets which
are themselves streaming (e.g. chunks of rows from a database, lines
from a file) without exploding memory.
"""
from __future__ import unicode_literals

from .core import glom


class Iter(object):
	"""
	Given an iterable target, yields the result of applying the passed
	spec to each element of the target.

	Basically, a lazy version of the default list-spec behavior.
	"""
	def __init__(self, spec):
		self.spec = spec

	def glomit(self, target, scope):
		for sub in target:
			yield scope[glom](target, self.spec, scope)
