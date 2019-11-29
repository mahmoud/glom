from glom import glom, S
from glom.trace import line_stack


def test_traces():
	stacklifier = ([{'data': S}],)
	scope = glom([1], stacklifier)[0]['data']
	raise Exception(line_stack(scope))
