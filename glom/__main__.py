
import os
import sys

from glom.cli import main

_enable_debug = os.getenv('GLOM_ENABLE_DEBUG')

if __name__ == '__main__':
    if _enable_debug:
        print(sys.argv)
    try:
        sys.exit(main(sys.argv) or 0)
    except Exception:
        if _enable_debug:
            import pdb;pdb.post_mortem()
        raise
