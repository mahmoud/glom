# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import subprocess

import pytest
from face import CommandChecker, CommandLineError

from glom import cli


BASIC_TARGET = '{"a": {"b": "c"}}'
BASIC_SPEC = '{"a": "a.b"}'
BASIC_OUT = '{"a": "c"}\n'

@pytest.fixture
def cc():
    cmd = cli.get_command()
    return CommandChecker(cmd)


def test_cli_spec_target_argv_basic(cc):
    res = cc.run(['glom', '--indent', '0', BASIC_SPEC, BASIC_TARGET])
    assert res.stdout == BASIC_OUT


def test_cli_spec_argv_target_stdin_basic(cc):
    res = cc.run(['glom', '--indent', '0', BASIC_SPEC],
                 input=BASIC_TARGET)
    assert res.stdout == BASIC_OUT


def test_cli_spec_target_files_basic(cc, tmp_path):
    spec_path = str(tmp_path) + '/spec.txt'
    with open(spec_path, 'w') as f:
        f.write(BASIC_SPEC)

    target_path = str(tmp_path) + '/target.txt'
    with open(target_path, 'w') as f:
        f.write(BASIC_TARGET)

    res = cc.run(['glom', '--indent', '0', '--target-file', target_path, '--spec-file', spec_path])
    assert res.stdout == BASIC_OUT


def test_main_basic():
    argv = ['__', 'a.b.fail', '{"a": {"b": "c"}}']
    assert cli.main(argv) == 1

    argv = ['__', 'a.b.c', '{"a": {"b": {"c": "d"}}}']
    assert cli.main(argv) == 0


def test_main_yaml_target():
    cwd = os.path.dirname(os.path.abspath(__file__))
    # Handles the filepath if running tox
    if '.tox' in cwd:
        cwd = os.path.join(cwd.split('.tox')[0] + '/glom/test/')
    path = os.path.join(cwd, 'data/test_valid.yaml')
    argv = ['__', '--target-file', path, '--target-format', 'yml', 'Hello']
    assert cli.main(argv) == 0

    path = os.path.join(cwd, 'data/test_invalid.yaml')
    argv = ['__', '--target-file', path, '--target-format', 'yml', 'Hello']
    # Makes sure correct improper yaml exception is raised
    with pytest.raises(CommandLineError) as excinfo:
        cli.main(argv)
    assert 'expected <block end>, but found' in str(excinfo.value)


def test_main_python_full_spec_python_target():
    argv = ['__', '--target-format', 'python', '--spec-format', 'python-full', 'T[T[3].bit_length()]', '{1: 2, 2: 3, 3: 4}']
    assert cli.main(argv) == 0

    argv = ['__', '--target-format', 'python', '--spec-format', 'python-full', '(T.values(), [T])', '{1: 2, 2: 3, 3: 4}']
    assert cli.main(argv) == 0


def test_main(tmp_path):
    # TODO: pytest-cov knows how to make coverage work across
    # subprocess boundaries...
    os.chdir(str(tmp_path))
    res = subprocess.check_output(['glom', 'a', '{"a": 3}'])
    assert res.decode('utf8') == '3\n'
