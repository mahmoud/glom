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


def _norm_stack(formatted_stack, exc):
    normalized = []
    for line in formatted_stack.split('\n'):
        if line.strip().startswith('File'):
            file_name = line.split('"')[1]
            short_file_name = os.path.split(file_name.strip('"'))[1]
            line = line.replace(file_name, short_file_name)
            line = line.partition('line')[0] + 'line ___,' + line.partition('line')[2].partition(',')[2]
        line = line.partition('0x')[0]  # scrub memory addresses

        line = line.rstrip()  # trailing whitespace shouldn't matter

        # qualify python2's unqualified error type names
        exc_type_name = exc.__class__.__name__
        if exc_type_name in line:
            mod_name = getattr(exc.__class__, '__module__', '') or ''
            exc_type_qual_name = exc_type_name
            if 'builtin' not in mod_name:
                exc_type_qual_name = mod_name + '.' + exc_type_name
            if exc_type_qual_name not in line:
                line = line.replace(exc_type_name, exc_type_qual_name)

        normalized.append(line)

    stack = "\n".join(normalized)
    stack = stack.replace(',)', ')')  # py37 likes to do Exception('msg',)
    return stack


def _make_stack(spec):
    try:
        glom([None], spec)
    except GlomError as e:
        stack = _norm_stack(traceback.format_exc(), e)
    return stack


def test_regular_error_stack():
    # ZeroDivisionError
    assert _make_stack({'results': [{'value': lambda t: 1/0}]}) == """\
Traceback (most recent call last):
  File "test_trace.py", line ___, in _make_stack
    glom([None], spec)
  File "core.py", line ___, in glom
    raise err
glom.core.GlomError.wrap(ZeroDivisionError):
-> {'results': [{'value': <function test_regular_error_stack.<locals>....
[None]
-> [{'value': <function test_regular_error_stack.<locals>.<lambda> at ...
-> {'value': <function test_regular_error_stack.<locals>.<lambda> at 0...
None
-> <function test_regular_error_stack.<locals>.<lambda> at
  File "core.py", line ___, in AUTO
    return spec(target)
  File "test_trace.py", line ___, in <lambda>
    assert _make_stack({'results': [{'value': lambda t: 1/0}]}) == \"""\\
ZeroDivisionError: division by zero
"""


def test_glom_error_stack():
    # NoneType has not attribute value
    expected = """\
Traceback (most recent call last):
  File "test_trace.py", line ___, in _make_stack
    glom([None], spec)
  File "core.py", line ___, in glom
    raise err
glom.core.PathAccessError:
-> {'results': [{'value': 'value'}]}
[None]
-> [{'value': 'value'}]
-> {'value': 'value'}
None
-> 'value'
  File "core.py", line ___, in AUTO
    return Path.from_text(spec).glomit(target, scope)
  File "core.py", line ___, in glomit
    return _t_eval(target, self.path_t, scope)
  File "core.py", line ___, in _t_eval
    raise pae
glom.core.PathAccessError: could not access 'value', part 0 of Path('value'), got error: AttributeError("'NoneType' object has no attribute 'value'")
"""
    actual = _make_stack({'results': [{'value': 'value'}]})
    assert actual == expected


def test_double_glom_error_stack():
    def uses_another_glom():
        return glom([None], {'internal': ['val']})
    def wrap():
        return uses_another_glom()
    assert _make_stack({'results': [{'value': lambda t: wrap()}]}) == """\
Traceback (most recent call last):
  File "test_trace.py", line ___, in _make_stack
    glom([None], spec)
  File "core.py", line ___, in glom
    raise err
glom.core.PathAccessError:
-> {'results': [{'value': <function test_double_glom_error_stack.<loca...
[None]
-> [{'value': <function test_double_glom_error_stack.<locals>.<lambda>...
-> {'value': <function test_double_glom_error_stack.<locals>.<lambda> ...
None
-> <function test_double_glom_error_stack.<locals>.<lambda> at
  File "core.py", line ___, in AUTO
    return spec(target)
  File "test_trace.py", line ___, in <lambda>
    assert _make_stack({'results': [{'value': lambda t: wrap()}]}) == \"""\\
  File "test_trace.py", line ___, in wrap
    return uses_another_glom()
  File "test_trace.py", line ___, in uses_another_glom
    return glom([None], {'internal': ['val']})
  File "core.py", line ___, in glom
    raise err
glom.core.PathAccessError:
-> {'internal': ['val']}
[None]
-> ['val']
-> 'val'
None
  File "core.py", line ___, in AUTO
    return Path.from_text(spec).glomit(target, scope)
  File "core.py", line ___, in glomit
    return _t_eval(target, self.path_t, scope)
  File "core.py", line ___, in _t_eval
    raise pae
glom.core.PathAccessError: could not access 'val', part 0 of Path('val'), got error: AttributeError("'NoneType' object has no attribute 'val'")
"""
