#!/usr/bin/env python3

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm


# ---------------------------------------------------------------------------
# Interactive sprite selection
# ---------------------------------------------------------------------------

def build_tree(files: list[Path]) -> dict:
    """Build a nested tree from file stems, splitting on '_' and dropping the last part."""
    tree: dict = {}
    for f in files:
        parts = f.stem.split("_")[:-1]
        d = tree
        for part in parts:
            d = d.setdefault(part, {})
        d.setdefault("__files__", []).append(f)
    return tree


def collect_all(node: dict) -> list[Path]:
    """Recursively collect all Path objects under a tree node."""
    result: list[Path] = []
    for key, val in node.items():
        if key == "__files__":
            result.extend(val)
        else:
            result.extend(collect_all(val))
    return result


def select_sprites(tree: dict, path: list[str] | None = None) -> list[Path]:
    """Interactively select sprites from the tree. Returns the selected Path list."""
    if path is None:
        path = []

    breadcrumb = " > ".join(path) if path else "root"
    sub_keys = sorted(k for k in tree if k != "__files__")
    direct_files = tree.get("__files__", [])

    # Pure leaf: only direct files, no sub-categories
    if not sub_keys:
        print(f"\n[{breadcrumb}]  ({len(direct_files)} files, no sub-categories)")
        choice = input("  Include all? [Y/n]: ").strip().lower()
        return list(direct_files) if choice in ("", "y", "yes") else []

    total = len(collect_all(tree))
    print(f"\n[{breadcrumb}]  ({total} files total)")
    if direct_files:
        print(f"  (+ {len(direct_files)} uncategorized files at this level)")
    print()
    print("   0) All")
    for i, key in enumerate(sub_keys, 1):
        count = len(collect_all(tree[key]))
        print(f"  {i:2}) {key}  ({count} files)")
    print()

    raw = input("Select (numbers or 0=all, comma/space-separated; Enter=skip): ").strip()

    if not raw:
        return []

    tokens = raw.replace(",", " ").split()

    if "0" in tokens:
        return collect_all(tree)

    selected: list[Path] = []
    seen_indices: set[int] = set()
    for tok in tokens:
        try:
            idx = int(tok)
        except ValueError:
            print(f"  (ignored: {tok!r})")
            continue
        if idx < 1 or idx > len(sub_keys):
            print(f"  (out of range: {idx})")
            continue
        if idx in seen_indices:
            continue
        seen_indices.add(idx)

        key = sub_keys[idx - 1]
        subtree = tree[key]
        sub_sub_keys = [k for k in subtree if k != "__files__"]
        if sub_sub_keys:
            # Has children — recurse so user can narrow down further
            selected.extend(select_sprites(subtree, path + [key]))
        else:
            # Leaf subtree — take everything
            selected.extend(collect_all(subtree))

    return selected


def fmt_size(b: int) -> str:
    if b < 1024 ** 2:
        return f"{b / 1024:.1f}KB"
    elif b < 1024 ** 3:
        return f"{b / 1024 ** 2:.1f}MB"
    else:
        return f"{b / 1024 ** 3:.2f}GB"


def convert_file(bin_dir: Path, palettes_path: Path, sld_file: Path, out_dir: Path) -> int:
    """Returns output file size in bytes on success, 0 on failure."""
    out_file = out_dir / f"{sld_file.stem}.png"
    cmd = [
        "./run", "convert-file",
        "--palettes-path", str(palettes_path),
        str(sld_file),
        str(out_file),
    ]
    try:
        subprocess.run(cmd, cwd=bin_dir, check=True, capture_output=True)
        return out_file.stat().st_size
    except (subprocess.CalledProcessError, OSError):
        return 0


def main():
    parser = argparse.ArgumentParser(description="Convert .sld graphics to .png sprites using openage")
    parser.add_argument("openage_dir", type=Path, help="Path to the openage directory")
    parser.add_argument("game_dir", type=Path, help="Path to the game directory")
    parser.add_argument("out_dir", type=Path, help="Output directory for .png files")
    parser.add_argument("--workers", type=int, default=16, help="Number of parallel workers (default: 16)")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactively select which sprites to convert")
    args = parser.parse_args()

    run_bin = args.openage_dir / "bin" / "run"
    if not run_bin.exists():
        print(f"Error: {run_bin} does not exist", file=sys.stderr)
        sys.exit(1)

    palettes_path = args.game_dir / "Tools_Builds" / "Sprites" / "_palettes"
    graphics_dir = args.game_dir / "resources" / "_common" / "drs" / "graphics"

    if not graphics_dir.exists():
        print(f"Error: graphics directory {graphics_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    sld_files = sorted(graphics_dir.glob("*.sld"))
    if not sld_files:
        print(f"No .sld files found in {graphics_dir}", file=sys.stderr)
        sys.exit(1)

    if args.interactive:
        tree = build_tree(sld_files)
        print("Select sprites to convert (Enter=skip a category, 0=select all):")
        sld_files = select_sprites(tree)
        if not sld_files:
            print("No sprites selected. Exiting.")
            sys.exit(0)
        print(f"\nSelected {len(sld_files)} file(s).")

    out_dir = args.out_dir.resolve()
    bin_dir = args.openage_dir / "bin"
    completed = 0
    failed = 0
    bytes_written = 0

    print(f"Input:   {graphics_dir}")
    print(f"Output:  {out_dir}")
    print(f"Total:   {len(sld_files)} .sld files")
    print(f"Workers: {args.workers}")

    with tqdm(total=len(sld_files), unit="file", dynamic_ncols=True) as progress:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(convert_file, bin_dir, palettes_path, sld_file, out_dir): sld_file
                for sld_file in sld_files
            }
            for future in as_completed(futures):
                size = future.result()
                if size > 0:
                    completed += 1
                    bytes_written += size
                else:
                    failed += 1
                projected = int(bytes_written / completed * len(sld_files)) if completed > 0 else 0
                progress.update(1)
                progress.set_postfix(done=completed, failed=failed,
                                     size=fmt_size(bytes_written), proj=fmt_size(projected))

    print(f"Done: {completed} converted, {failed} failed")
    print(f"Size: {fmt_size(bytes_written)} written  |  projected total: {fmt_size(int(bytes_written / completed * len(sld_files)) if completed else 0)}")


if __name__ == "__main__":
    main()
