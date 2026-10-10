"""API runner script for SkillGap FastAPI server."""

import subprocess
import sys


def main() -> None:
    args = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ] + sys.argv[1:]
    sys.exit(subprocess.call(args))


if __name__ == "__main__":
    main()
