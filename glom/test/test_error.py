
import pytest

from glom import glom, T, GlomError

@pytest.mark.xfail
def test_good_error():
    target = {'data': [0, 1, 2]}

    glom(target, ('data.3'))


@pytest.mark.xfail
def test_error():
    target = {'data': [0, 1, 2]}

    glom(target, ('data', '3'))
    glom(target, ('data', [(T.real, T.bit_length, T.image)]))
