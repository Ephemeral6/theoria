"""`python -m proxy.scoring` -- a package needs this to be executable."""

import sys

from . import main

if __name__ == "__main__":
    sys.exit(main())
