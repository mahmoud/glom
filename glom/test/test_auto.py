'''
Use hypothesis and contracts to automatically search for flaws.
'''
from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from glom import glom, Inspect, Coalesce, T


class SpecAndTarget(RuleBasedStateMachine):
	'''
	auto generate a spec and target that should work together
	need more sophisticated strategies to make this more useful
	(probably not mindless recursion to an arbitrary depth)
	'''
	def __init__(self):
		super(SpecAndTarget, self).__init__()
		self.spec = T
		self.target = None
		self.result = None

	@invariant()
	def spec_works(self):
		assert glom(self.target, self.spec) == self.result

	@rule()
	def add_inspect(self):
		self.spec = Inspect(self.spec)

	@rule()
	def add_list(self):
		self.spec = [self.spec]
		self.target = [self.target, self.target]
		self.result = [self.result, self.result]

	@rule()
	def add_dict(self):
		self.spec = {'key': self.spec}
		self.result = {'key': self.result}

	@rule()
	def add_coalesce(self):
		self.spec = Coalesce(self.spec)

	@rule()
	def add_tuple(self):
		self.spec = (self.spec, T)


TestSpecAndTarget = SpecAndTarget.TestCase
TestSpecAndTarget.settings = settings(max_examples=20, stateful_step_count=50)
