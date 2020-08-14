
from glom import glom, T

spec = T['a']['b']['c']

target = {'a': {'b': {'c': 'd'}}}

output = glom(target, spec)
assert output == 'd'

output = glom(target, T['a']['b']['c'].upper())
assert output == 'D'

output = glom(target, T['z'].upper(), default=None)
assert output is None



from glom import glom, Iter

target = ['1', '2', '1', '3']

spec = Iter().map(int).unique().all()

output = glom(target, spec)
assert output == [1, 2, 3]
