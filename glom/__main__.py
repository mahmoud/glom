
import os
import sys

from glom.core import main

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv) or 0)
    except Exception:
        if os.getenv('GLOM_ENABLE_DEBUG'):
            import pdb;pdb.post_mortem()
        raise
