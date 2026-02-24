#!/usr/bin/env python3
"""
Initialize the genie-backend project by extracting genieutils + pcrio
from the AoE2DE tools and patching them for Linux.
"""

import subprocess
import sys
from pathlib import Path

GAME_PATH = Path.home() / ".steam/steam/steamapps/common/AoE2DE"
ARCHIVE = GAME_PATH / "Tools_Builds/docs/Source.7z"
PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_DIR / "Source"


def main() -> int:
    if not ARCHIVE.exists():
        print(f"Error: archive not found: {ARCHIVE}")
        return 1

    if SOURCE_DIR.exists():
        print(f"Source/ already exists, skipping extraction.")
    else:
        print(f"Extracting {ARCHIVE} ...")
        result = subprocess.run(
            ["7z", "x", str(ARCHIVE), f"-o{SOURCE_DIR}"],
            cwd=PROJECT_DIR,
        )
        if result.returncode != 0:
            print("Extraction failed.")
            return 1

    # Verify expected directories exist
    for name in ("genieutils", "pcrio"):
        d = SOURCE_DIR / name
        if not d.is_dir():
            print(f"Error: expected directory not found: {d}")
            return 1
        print(f"Found {d.relative_to(PROJECT_DIR)}/")

    # Run patch_linux.py
    patch_script = PROJECT_DIR / "patch_linux.py"
    print(f"\nRunning {patch_script.name} ...")
    result = subprocess.run(
        [sys.executable, str(patch_script), "--source-dir", str(SOURCE_DIR)],
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print("Patching failed.")
        return result.returncode

    print("\nDone. You can now build with:")
    print("  cmake -B build && cmake --build build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
