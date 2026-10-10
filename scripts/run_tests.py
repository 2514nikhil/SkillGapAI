"""Test runner script for SkillGap."""

import subprocess
import sys


def main() -> None:
    args = [sys.executable, "-m", "pytest", "-v"] + sys.argv[1:]
    sys.exit(subprocess.call(args))


if __name__ == "__main__":
    main()
