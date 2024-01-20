# assignment

from glom import glom, Assign

target = {'a': [{'b': 'c'}, {'d': None}]}

# let's set the 'd' key to 'e'
glom(target, Assign('a.1.d', 'e'))

assert target['a'][1]['d'] == 'e'


from glom import Spec

# let's assign one target value to another target value
glom(target, Assign('a.1.d', Spec('a.0.b')))

assert target['a'] == [{'b': 'c'}, {'d': 'c'}]


# Iter

from glom import glom, Iter

target = ['1', '2', '1', '3']

spec = Iter().map(int).unique().all()

output = glom(target, spec)
assert output == [1, 2, 3]

# T

from glom import glom, T

target = {'a': {'b': {'c': 'd'}}}

spec = T['a']['b']['c']

output = glom(target, spec)
assert output == 'd'

output = glom(target, T['a']['b']['c'].upper())
assert output == 'D'

output = glom(target, T['z'].upper(), default=None)
assert output is None


class Contact(object):
    def __init__(self, name, details_dict):
        self.name = name
        self.details = details_dict

frank = Contact('Frank', {'emails': ['FRANK@NothingButHotdogs.BIZ']})

output = glom(frank, T.details['emails'][0].lower())
assert output == 'frank@nothingbuthotdogs.biz'
