
import pytest

from glom import glom, T, GlomError


def test_good_error():
    target = {'data': [0, 1, 2]}

    with pytest.raises(GlomError):
        glom(target, ('data.3'))


def test_error():
    target = {'data': [0, 1, 2]}

    with pytest.raises(GlomError):
        glom(target, ('data', '3'))
    with pytest.raises(GlomError):
        glom(target, ('data', [(T.real, T.bit_length, T.image)]))


def test_unfinalized_glomerror_repr():
    assert 'GlomError()' in repr(GlomError())
