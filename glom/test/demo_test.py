"""
structured demo code as tests to keep us honest in ohnly showing working code
"""
import json

import pytest

from glom import Ref, Match, Switch, Auto, T, glom, Or, GlomError, M, And



def test_json_check():
    # we can define a self-recursive spec that
    # checks a data structure for JSON compatibility
    json_spec = Match(Ref(
        'json', Switch({
            dict: {str: Ref('json')},
            list: [Ref('json')],
            Or(int, float, str): T,
        })
    ))
    glom({'customers': ['alice', 'bob']}, json_spec)
    # why might we want to do this?
    # first, we get a nice error tree
    # we also have very fine grained control over behaviors
    # maybe we want to be more strict than the standard library
    json.dumps({1: 1})  # {"1": 1}
    with pytest.raises(GlomError):
        glom({1: 1}, json_spec)
    # maybe we want to customize a little bit
    # for example, lets say we want to ensure that
    # integers are 'float-safe' (can be losslessly
    # converted to an IEEE 754 double precision float)
    json_spec = Match(Ref(
        'json', Switch({
            dict: {str: Ref('json')},
            list: [Ref('json')],
            Or(float, str): T,
            And(int, M > - 2 ** 52, M < 2 ** 52): T,
        })
    ))
    glom(2**51, json_spec)
    with pytest.raises(GlomError):
        glom(2**52, json_spec)
