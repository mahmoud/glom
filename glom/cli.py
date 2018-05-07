"""like jq, but with the full power of python in the spec.

Usage: python -m glom [FLAGS] [spec [target]]

Command-line interface to the glom library, providing nested data
access and data restructuring with the power of Python.


Flags:

  --help / -h                 show this help message and exit
  --target-file TARGET_FILE   path to target data source (optional)
  --target-format TARGET_FORMAT
                              format of the source data (json or python)
                              (defaults to 'json')
  --spec-file SPEC_FILE       path to glom spec definition (optional)
  --spec-format SPEC_FORMAT   format of the glom spec definition (json, python,
                              python-full) (defaults to 'python')
  --indent INDENT             number of spaces to indent the result, 0 to disable
                              pretty-printing (defaults to 2)
  --debug                     interactively debug any errors that come up
  --inspect                   interactively explore the data

try out:

curl -s https://api.github.com/repos/mahmoud/glom/events | python -m glom '[{"type": "type", "date": "created_at", "user": "actor.login"}]'

"""


from __future__ import print_function

import os
import ast
import sys
import json

from face import Command, Flag, face_middleware, PosArgSpec, PosArgDisplay
from face.command import CommandLineError

from glom import glom, Path, GlomError, Inspect

def glom_cli(target, spec, indent, debug, inspect):
    """Command-line interface to the glom library, providing nested data
    access and data restructuring with the power of Python.
    """
    if debug or inspect:
        stdin_open = not sys.stdin.closed
        spec = Inspect(spec,
                       echo=inspect,
                       recursive=inspect,
                       breakpoint=inspect and stdin_open,
                       post_mortem=debug and stdin_open)

    try:
        result = glom(target, spec)
    except GlomError as ge:
        print('%s: %s' % (ge.__class__.__name__, ge))
        return 1

    if not indent:
        indent = None
    print(json.dumps(result, indent=indent, sort_keys=True))
    return


def main(argv):
    posargs = PosArgSpec(str, max_count=2, display={'label': '[spec [target]]'})
    cmd = Command(glom_cli, posargs=posargs, middlewares=[mw_get_target])
    cmd.add('--target-file', str, missing=None, doc='path to target data source')
    cmd.add('--target-format', str, missing='json',
            doc='format of the source data (json or python)')
    cmd.add('--spec-file', str, missing=None, doc='path to glom spec definition')
    cmd.add('--spec-format', str, missing='python',
            doc='format of the glom spec definition (json, python, python-full)')

    cmd.add('--indent', int, missing=2,
            doc='number of spaces to indent the result, 0 to disable pretty-printing')

    cmd.add('--debug', parse_as=True, doc='interactively debug any errors that come up')
    cmd.add('--inspect', parse_as=True, doc='interactively explore the data')

    return cmd.run(argv) or 0


def console_main():
    _enable_debug = os.getenv('GLOM_ENABLE_DEBUG')
    if _enable_debug:
        print(sys.argv)
    try:
        sys.exit(main(sys.argv) or 0)
    except Exception:
        if _enable_debug:
            import pdb;pdb.post_mortem()
        raise


def _error(msg):
    # TODO: build this functionality into face
    print('error:', msg)
    raise CommandLineError(msg)


@face_middleware(provides=['spec', 'target'])
def mw_get_target(next_, posargs_, target_file, target_format, spec_file, spec_format):
    spec_text, target_text = None, None
    if len(posargs_) == 2:
        spec_text, target_text = posargs_
    elif len(posargs_) == 1:
        spec_text, target_text = posargs_[0], None

    if spec_text and spec_file:
        _error('expected spec file or spec argument, not both')
    elif spec_file:
        try:
            with open(spec_file, 'r') as f:
                spec_text = f.read()
        except IOError as ose:
            _error('could not read spec file %r, got: %s' % (spec_file, ose))

    if not spec_text:
        spec = Path()
    elif spec_format == 'python':
        if spec_text[0] not in ('"', "'", "[", "{", "("):
            # intention: handle trivial path access, assume string
            spec_text = repr(spec_text)
        spec = ast.literal_eval(spec_text)
    elif spec_format == 'json':
        spec = json.loads(spec_text)
    else:
        _error('expected spec-format to be one of python or json')

    if target_text and target_file:
        _error('expected target file or target argument, not both')
    elif target_text == '-' or target_file == '-':
        with sys.stdin as f:
            target_text = f.read()
    elif target_file:
        try:
            target_text = open(target_file, 'r').read()
        except IOError as ose:
            _error('could not read target file %r, got: %s' % (target_file, ose))
    elif not target_text and not os.isatty(sys.stdin.fileno()):
        with sys.stdin as f:
            target_text = f.read()

    if not target_text:
        target = {}
    elif target_format == 'json':
        try:
            target = json.loads(target_text)
        except Exception as e:
            _error('could not load target data, got: %s' % e)
    else:
        _error('expected spec-format to be one of python or json')

    return next_(spec=spec, target=target)
