import pytest

from glom import Vars, glom


@pytest.mark.parametrize('factory', [iter, lambda pairs: (pair for pair in pairs)])
def test_vars_retains_iterator_initial_values_across_evaluations(factory):
    shared = []
    spec = Vars(factory([('name', 'alice'), ('shared', shared)]), name='override')
    for _ in range(2):
        result = dict(glom(None, spec))
        assert result['name'] == 'override'
        assert result['shared'] is shared


def test_vars_retains_existing_mapping_reference():
    base = {'value': 1}
    spec = Vars(base)
    base['value'] = 2
    assert dict(glom(None, spec)) == {'value': 2}


def test_vars_empty_iterator_and_invalid_pairs():
    assert dict(glom(None, Vars(iter(()), value=1))) == {'value': 1}
    with pytest.raises(ValueError):
        Vars(iter([('a', 1, 2)]))
