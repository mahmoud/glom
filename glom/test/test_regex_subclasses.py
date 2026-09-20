import pytest

from glom import MatchError, Regex, glom


class Text(str):
    pass


class Bytes(bytes):
    pass


@pytest.mark.parametrize('value,pattern', [(Text('abc'), 'abc'), (Bytes(b'abc'), b'abc')])
def test_regex_accepts_string_subclasses(value, pattern):
    assert glom(value, Regex(pattern)) is value


@pytest.mark.parametrize('value,pattern', [(Text('abc'), 'def'), (Bytes(b'abc'), b'def')])
def test_regex_nonmatching_subclass_still_raises(value, pattern):
    with pytest.raises(MatchError):
        glom(value, Regex(pattern))
