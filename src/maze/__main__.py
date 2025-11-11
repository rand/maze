"""Allow running maze as a module: python -m maze"""

import sys

from maze.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
