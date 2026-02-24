#!/usr/bin/env python3
"""
Patch script to make genieutils + pcrio compile on Linux.

Idempotent — safe to rerun after source updates.
Run from the Source/ directory (or pass --source-dir).
"""

import argparse
import sys
from pathlib import Path


def patch_file(filepath: Path, anchor: str, insertion: str, label: str) -> bool:
    """Insert `insertion` after `anchor` in file, if not already present.

    Returns True if patch was applied or already present, False on error.
    """
    if not filepath.exists():
        print(f"  SKIP  {label}: file not found ({filepath})")
        return False

    text = filepath.read_text()

    # Already patched?
    if insertion.strip() in text:
        print(f"  OK    {label}: already applied")
        return True

    # Find anchor
    idx = text.find(anchor)
    if idx == -1:
        print(f"  FAIL  {label}: anchor not found")
        return False

    insert_pos = idx + len(anchor)
    patched = text[:insert_pos] + "\n" + insertion + text[insert_pos:]
    filepath.write_text(patched)
    print(f"  PATCH {label}: applied")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Path to the Source/ directory (default: script location)",
    )
    args = parser.parse_args()
    source: Path = args.source_dir

    print(f"Source directory: {source}")
    ok = True

    # --- Patch 1: pcrio/pcrio.c — fopen_s compat macro ---
    ok &= patch_file(
        filepath=source / "pcrio" / "pcrio.c",
        anchor='#include "pcrio.h"',
        insertion=(
            "\n"
            "/* Linux compat: MSVC secure CRT functions */\n"
            "#ifndef _MSC_VER\n"
            "#define fopen_s(pFile, filename, mode) \\\n"
            "    ((*(pFile) = fopen((filename), (mode))) == NULL)\n"
            "#define strncpy_s(dest, destsz, src, count) strncpy((dest), (src), (count))\n"
            "#define strcpy_s(dest, destsz, src) strcpy((dest), (src))\n"
            "#endif\n"
        ),
        label="pcrio.c MSVC secure CRT compat",
    )

    # --- Patch 2: genieutils CMakeLists.txt — missing source files ---
    ok &= patch_file(
        filepath=source / "genieutils" / "CMakeLists.txt",
        anchor="src/dat/unit/Building.cpp",
        insertion="    src/dat/unit/TrainLocation.cpp\n    src/dat/ResearchLocation.cpp",
        label="genieutils CMakeLists.txt missing sources",
    )

    # Summary
    print()
    if ok:
        print("All patches applied successfully.")
        return 0
    else:
        print("Some patches failed — see above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
