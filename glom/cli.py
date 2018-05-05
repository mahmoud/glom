
import ast
import json

from glom import glom, Path, GlomError


def main(argv):
    """glom.py [FLAGS]] <spec> <target>
    TODO:

    --unsafe  (does a full eval() of spec, with many glom builtins available)
    --target-file <path> (can be -)
    --target-format  (anything other than json out there?)
    --indent <num_of_spaces> (defaults to 2)
    --debug (Inspect post mortem)
    --inspect  (Inspect breakpoint)

    if target-file is not set, target is either what's on the command
    line, or stdin.
    (i.e., if not os.isatty(sys.stdin.fileno()): sys.stdin.read()
    or something)

    results come out on stdout, but errors and any trace/debug info
    should be on stderr, at least in CLI mode.

    """
    spec_text = argv[1]
    target_text = argv[2]


    if not spec_text:
        spec = Path()
    else:
        if spec_text[0] not in ('"', "'", "[", "{", "("):
            # intention: handle trivial path access, assume string
            spec_text = repr(spec_text)
        spec = ast.literal_eval(spec_text)

    target = json.loads(target_text)

    try:
        result = glom(target, spec)
    except GlomError as ge:
        print('%s: %s' % (ge.__class__.__name__, ge))
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))

    return 0
