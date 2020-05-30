import os
import traceback

import pytest

from glom import glom, S, Coalesce, GlomError
from glom.trace import line_stack, short_stack, tall_stack


@pytest.mark.skip
def test_trace_basic():
    try:
        glom({}, 'a')
    except GlomError as ge:
        _ge = ge
        fmtd = traceback.format_exc()
        import pdb;pdb.set_trace()
        raise
    else:
        raise RuntimeError()

def test_line_trace():
    stacklifier = ([{'data': S}],)
    scope = glom([1], stacklifier)[0]['data']
    fmtd_stack = line_stack(scope)
    assert fmtd_stack == '/tuple!list/list<0>/dict!int/S'


def test_short_trace():
    stacklifier = ([{'data': S}],)
    scope = glom([1], stacklifier)[0]['data']
    fmtd_stack = short_stack(scope)
    exp_lines = ["-> ([{'data': S}],)",
                 "[1]",
                 "-> [{'data': S}]",
                 "-> {'data': S}",
                 "1",
                 "-> S"]
    assert fmtd_stack.splitlines() == exp_lines

def test_tall_trace():
    stacklifier = ([{'data': S}],)
    scope = glom([1], stacklifier)[0]['data']
    fmtd_stack = tall_stack(scope)
    exp_lines = ["-> ([{'data': S}],)",
                 "[1]",
                 "-> [{'data': S}]",
                 "-> {'data': S}",
                 "1",
                 "-> S"]
    assert fmtd_stack.splitlines() == exp_lines


def _err(inp, depth=3):
    if depth == 0:
        raise ValueError(inp)
    _err(inp, depth - 1)


def _norm_stack(formatted_stack):
    normalized = []
    for line in formatted_stack.split('\n'):
        if line.strip().startswith('File'):
            file_name = line.split('"')[1]
            short_file_name = os.path.split(file_name.strip('"'))[1]
            line = line.replace(file_name, short_file_name)
        line = line.partition('0x')[0]  # scrub memory addresses
        normalized.append(line)
    return "\n".join(normalized)


def _make_stack(spec):
    try:
        glom([None], spec)
    except GlomError:
        stack = _norm_stack(traceback.format_exc())
    return stack


def test_regular_error_stack():
    # ZeroDivisionError
    assert _make_stack({'results': [{'value': lambda t: 1/0}]}) == """\
Traceback (most recent call last):
  File "test_trace.py", line 74, in _make_stack
    glom([None], spec)
  File "core.py", line 1893, in glom
    raise err
glom.core.GlomWrapError: 
-> {'results': [{'value': <function test_regular_error_stack.<locals>....
[None]
-> [{'value': <function test_regular_error_stack.<locals>.<lambda> at ...
-> {'value': <function test_regular_error_stack.<locals>.<lambda> at 0...
None
-> <function test_regular_error_stack.<locals>.<lambda> at 
  File "core.py", line 1927, in AUTO
    return spec(target)
  File "test_trace.py", line 82, in <lambda>
    assert _make_stack({'results': [{'value': lambda t: 1/0}]}) == \"""\\
ZeroDivisionError: division by zero

"""


def test_glom_error_stack():
    # NoneType has not attribute value
    assert _make_stack({'results': [{'value': 'value'}]}) == """\
Traceback (most recent call last):
  File "test_trace.py", line 74, in _make_stack
    glom([None], spec)
  File "core.py", line 1893, in glom
    raise err
glom.core.PathAccessError: 
-> {'results': [{'value': 'value'}]}
[None]
-> [{'value': 'value'}]
-> {'value': 'value'}
None
-> 'value'
  File "core.py", line 1925, in AUTO
    return Path.from_text(spec).glomit(target, scope)
  File "core.py", line 422, in glomit
    return _t_eval(target, self.path_t, scope)
  File "core.py", line 1276, in _t_eval
    raise pae
glom.core.PathAccessError: could not access 'value', part 0 of Path('value'), got error: AttributeError("'NoneType' object has no attribute 'value'")
could not access 'value', part 0 of Path('value'), got error: AttributeError("'NoneType' object has no attribute 'value'")
"""


def test_double_glom_error_stack():
    def uses_another_glom():
        return glom([None], {'internal': ['val']})
    def wrap():
        return uses_another_glom()
    assert _make_stack({'results': [{'value': lambda t: wrap()}]}) == """\
Traceback (most recent call last):
  File "test_trace.py", line 74, in _make_stack
    glom([None], spec)
  File "core.py", line 1893, in glom
    raise err
glom.core.PathAccessError: 
-> {'results': [{'value': <function test_double_glom_error_stack.<loca...
[None]
-> [{'value': <function test_double_glom_error_stack.<locals>.<lambda>...
-> {'value': <function test_double_glom_error_stack.<locals>.<lambda> ...
None
-> <function test_double_glom_error_stack.<locals>.<lambda> at 
  File "core.py", line 1927, in AUTO
    return spec(target)
  File "test_trace.py", line 135, in <lambda>
    assert _make_stack({'results': [{'value': lambda t: wrap()}]}) == \"""\\
  File "test_trace.py", line 134, in wrap
    return uses_another_glom()
  File "test_trace.py", line 132, in uses_another_glom
    return glom([None], {'internal': ['val']})
  File "core.py", line 1893, in glom
    raise err
glom.core.PathAccessError: 
-> {'internal': ['val']}
[None]
-> ['val']
-> 'val'
None
  File "core.py", line 1925, in AUTO
    return Path.from_text(spec).glomit(target, scope)
  File "core.py", line 422, in glomit
    return _t_eval(target, self.path_t, scope)
  File "core.py", line 1276, in _t_eval
    raise pae
glom.core.PathAccessError: could not access 'val', part 0 of Path('val'), got error: AttributeError("'NoneType' object has no attribute 'val'")
could not access 'val', part 0 of Path('val'), got error: AttributeError("'NoneType' object has no attribute 'val'")
could not access 'val', part 0 of Path('val'), got error: AttributeError("'NoneType' object has no attribute 'val'")
"""
