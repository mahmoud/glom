# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from face import CommandChecker

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
