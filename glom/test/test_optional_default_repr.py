import pytest

from glom import Match, Optional, Val, glom


@pytest.mark.parametrize('default', [None, False, 0, '', [], 'fallback'])
def test_optional_default_survives_repr_round_trip(default):
    original = Optional('name', default=default)
    restored = eval(repr(original), {'Optional': Optional})
    assert glom({}, Match({original: object})) == {'name': default}
    assert glom({}, Match({restored: object})) == {'name': default}


def test_optional_spec_default_survives_repr_round_trip():
    original = Optional('name', default=Val('fallback'))
    restored = eval(repr(original), {'Optional': Optional, 'Val': Val})
    assert glom({}, Match({restored: str})) == {'name': 'fallback'}


def test_optional_without_default_keeps_existing_repr():
    assert repr(Optional('name')) == "Optional('name')"
