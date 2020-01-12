from glom import glom, S, Coalesce
from glom.trace import line_stack, short_stack, tall_stack


from glom.tutorial import CONTACTS


def test_line_trace():
    stacklifier = ([{'data': S}],)
    scope = glom([1], stacklifier)[0]['data']
    raise Exception(line_stack(scope))


def test_short_trace():
    stacklifier = ([{'data': S}],)
    scope = glom([1], stacklifier)[0]['data']
    raise Exception(short_stack(scope))


def test_tall_trace():
    stacklifier = ([{'data': S}],)
    scope = glom([1], stacklifier)[0]['data']
    raise Exception(tall_stack(scope))


def _err(inp, depth=3):
    if depth == 0:
        raise ValueError(inp)
    _err(inp, depth - 1)


SPEC = {'results': [{'id': 'id',
                     'name': 'name',
                     'add_date': ('add_date', str),
                     'emails': ('emails', [{'id': 'id',
                                            'email': 'email',
                                            'type': _err}]),
                     'primary_email': Coalesce('primary_email.email', default=None),
                     'pref_name': Coalesce('pref_name', 'name', skip='', default=''),
                     'detail': Coalesce('company',
                                        'location',
                                        ('add_date.year', str),
                                        skip='', default='')}]}


def test_in_situ():
    glom(CONTACTS, SPEC)
