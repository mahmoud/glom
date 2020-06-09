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
    exp_lines = [
        "   target: [1]",
        "   spec: ([{'data': S}],)",
        "   spec: [{'data': S}]",
        "   target: 1",
        "   spec: {'data': S}",
        "   spec: S",
    ]
    assert fmtd_stack.splitlines() == exp_lines

def test_tall_trace():
    stacklifier = ([{'data': S}],)
    scope = glom([1], stacklifier)[0]['data']
    fmtd_stack = tall_stack(scope)
    exp_lines = [
        "   target: [1]",
        "   spec: ([{'data': S}],)",
        "   spec: [{'data': S}]",
        "   target: 1",
        "   spec: {'data': S}",
        "   spec: S",
    ]
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


def _raise_exc(t):
    # had to go from zerodivision to this bc ZDE message changed
    # between 2 and 3
    raise Exception('unique message')


def test_regular_error_stack():
    assert _make_stack({'results': [{'value': _raise_exc}]}) == """\
Traceback (most recent call last):
  File "test_trace.py", line ___, in _make_stack
    glom([None], spec)
  File "core.py", line ___, in glom
    raise err
glom.core.GlomError.wrap(Exception):
   target: [None]
   spec: {'results': [{'value': <function _raise_exc at
   spec: [{'value': <function _raise_exc at
   target: None
   spec: {'value': <function _raise_exc at
   spec: <function _raise_exc at
  File "core.py", line ___, in AUTO
    return spec(target)
  File "test_trace.py", line ___, in _raise_exc
    raise Exception('unique message')
Exception: unique message
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
   target: [None]
   spec: {'results': [{'value': 'value'}]}
   spec: [{'value': 'value'}]
   target: None
   spec: {'value': 'value'}
   spec: 'value'
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


# used by the test below, but at the module level to make stack traces
# more uniform between py2 and py3 (py3 tries to qualify lambdas and
# other functions inside of local scopes.)
def _uses_another_glom():
    return glom([None], {'internal': ['val']})

def _subglom_wrap(t):
    return _uses_another_glom()


def test_double_glom_error_stack():
    assert _make_stack({'results': [{'value': _subglom_wrap}]}) == """\
Traceback (most recent call last):
  File "test_trace.py", line ___, in _make_stack
    glom([None], spec)
  File "core.py", line ___, in glom
    raise err
glom.core.PathAccessError:
   target: [None]
   spec: {'results': [{'value': <function _subglom_wrap at
   spec: [{'value': <function _subglom_wrap at
   target: None
   spec: {'value': <function _subglom_wrap at
   spec: <function _subglom_wrap at
  File "core.py", line ___, in AUTO
    return spec(target)
  File "test_trace.py", line ___, in _subglom_wrap
    return _uses_another_glom()
  File "test_trace.py", line ___, in _uses_another_glom
    return glom([None], {'internal': ['val']})
  File "core.py", line ___, in glom
    raise err
glom.core.PathAccessError:
   target: [None]
   spec: {'internal': ['val']}
   spec: ['val']
   target: None
   spec: 'val'
  File "core.py", line ___, in AUTO
    return Path.from_text(spec).glomit(target, scope)
  File "core.py", line ___, in glomit
    return _t_eval(target, self.path_t, scope)
  File "core.py", line ___, in _t_eval
    raise pae
glom.core.PathAccessError: could not access 'val', part 0 of Path('val'), got error: AttributeError("'NoneType' object has no attribute 'val'")
"""
