
import os
from glom.cli import main, console_main
import pytest
from face.command import CommandLineError


def test_main_basic():
    argv = ['__', 'a.b.fail', '{"a": {"b": "c"}}']
    assert main(argv) == 1

    argv = ['__', 'a.b.c', '{"a": {"b": {"c": "d"}}}']
    assert main(argv) == 0


def test_yaml_target():
    cwd = os.path.dirname(os.path.abspath(__file__))
    # Handles the filepath if running tox
    if '.tox' in cwd:
        cwd = os.path.join(cwd.split('.tox')[0] + '/glom/test/')
    path = os.path.join(cwd, 'data/test_valid.yaml')
    argv = ['__', '--target-file', path, '--target-format', 'yml', 'Hello']
    assert main(argv) == 0

    path = os.path.join(cwd, 'data/test_invalid.yaml')
    argv = ['__', '--target-file', path, '--target-format', 'yml', 'Hello']
    # Makes sure correct improper yaml exception is raised
    with pytest.raises(CommandLineError) as excinfo:
        main(argv)
    assert 'expected <block end>, but found' in str(excinfo.value)


def test_python_full_spec_python_target():
    argv = ['__', '--target-format', 'python', '--spec-format', 'python-full', 'T[T[3].bit_length()]', '{1: 2, 2: 3, 3: 4}']
    assert main(argv) == 0

    argv = ['__', '--target-format', 'python', '--spec-format', 'python-full', '(T.values(), [T])', '{1: 2, 2: 3, 3: 4}']
    assert main(argv) == 0
