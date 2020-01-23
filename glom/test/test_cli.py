# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from face import CommandChecker

from glom import cli

def test_cli():
    cmd = cli.get_command()
    cc = CommandChecker(cmd)

    res = cc.run(['glom', '--indent', '0', '{"a": "a.b"}', '{"a": {"b": "c"}}'])
    assert res.stdout == '{"a": "c"}\n'
