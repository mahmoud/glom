from functools import partial
from operator import eq, methodcaller

import pytest

from glom import Match, MatchError, Switch, Val, glom


class Predicate:
    def __call__(self, target):
        return target == 'yes'


@pytest.mark.parametrize('predicate, target', [
    (partial(eq, 'yes'), 'no'),
    (methodcaller('isdigit'), 'letters'),
    (Predicate(), 'no'),
    (methodcaller('isdigit'), 123),
])
def test_unnamed_callable_mismatch_supports_defaults(predicate, target):
    assert glom(target, Match(predicate, default='fallback')) == 'fallback'
    with pytest.raises(MatchError):
        glom(target, Match(predicate))


def test_unnamed_callable_mismatch_allows_switch_fallback():
    spec = Switch([(Match(partial(eq, 'yes')), Val('matched'))], default=Val('fallback'))
    assert glom('yes', spec) == 'matched'
    assert glom('no', spec) == 'fallback'


def test_named_callable_diagnostic_retains_name():
    with pytest.raises(MatchError, match='isdigit'):
        glom('letters', Match(str.isdigit))
