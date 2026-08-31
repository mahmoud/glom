"""Regression test for self-referential target dicts triggering RecursionError.

See: https://github.com/mahmoud/glom/issues/315
"""
import pytest
import glom


def test_self_referential_dict_recursion():
    """Self-referential dicts should not cause bare RecursionError.
    
    When the target contains a self-reference (e.g., d['self'] = d),
    glom() should either detect the cycle and raise a descriptive error,
    or handle it gracefully. A bare RecursionError without context is
    unacceptable.
    """
    # Create a self-referential dict
    d = {}
    d['self'] = d
    
    # This should not cause a bare RecursionError
    # Either it should work (with cycle detection) or raise a descriptive error
    with pytest.raises(Exception) as exc_info:
        glom.glom(d, ['self', 'self', 'self'], default='', skip_exc=None)
    
    # The exception should NOT be a bare RecursionError
    # It should either be handled gracefully or be a descriptive GlomError
    exc_type = type(exc_info.value)
    exc_str = str(exc_info.value)
    
    # If it's a RecursionError, it should have a descriptive message about cycles
    if exc_type is RecursionError:
        assert 'cycle' in exc_str.lower() or 'self-referential' in exc_str.lower() or 'visited' in exc_str.lower(), \
            f"Bare RecursionError without cycle detection message: {exc_str}"


def test_self_referential_list_recursion():
    """Self-referential lists should not cause bare RecursionError."""
    # Create a self-referential list
    lst = []
    lst.append(lst)
    
    with pytest.raises(Exception) as exc_info:
        glom.glom(lst, [0, 0, 0], default='', skip_exc=None)
    
    exc_type = type(exc_info.value)
    exc_str = str(exc_info.value)
    
    if exc_type is RecursionError:
        assert 'cycle' in exc_str.lower() or 'self-referential' in exc_str.lower() or 'visited' in exc_str.lower(), \
            f"Bare RecursionError without cycle detection message: {exc_str}"


def test_chained_reference_recursion():
    """Chained references (a['b'] = b; b['a'] = a) should not cause bare RecursionError."""
    a = {}
    b = {}
    a['b'] = b
    b['a'] = a
    
    with pytest.raises(Exception) as exc_info:
        glom.glom(a, ['b', 'a', 'b', 'a'], default='', skip_exc=None)
    
    exc_type = type(exc_info.value)
    exc_str = str(exc_info.value)
    
    if exc_type is RecursionError:
        assert 'cycle' in exc_str.lower() or 'self-referential' in exc_str.lower() or 'visited' in exc_str.lower(), \
            f"Bare RecursionError without cycle detection message: {exc_str}"
