"""Setup script to install dependencies, models, and generate fixtures."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> None:
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    python_exe = sys.executable

    print("Step 1: Installing dependencies from requirements.txt...")
    run_command([python_exe, "-m", "pip", "install", "-r", str(base_dir / "requirements.txt")])

    print("\nStep 2: Downloading spaCy en_core_web_sm model...")
    run_command([python_exe, "-m", "spacy", "download", "en_core_web_sm"])

    print("\nStep 3: Generating test fixtures...")
    run_command([python_exe, str(base_dir / "scripts" / "generate_fixtures.py")])

    print("\nSetup completed successfully!")


if __name__ == "__main__":
    main()
