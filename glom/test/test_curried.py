from glom import glom
from glom.curried import glom as glomc

spec = {'name': 'callsign'}
data = {'callsign': 'maverick'}


def test_curried():
    assert glomc(spec)(data) == glom(data, spec)