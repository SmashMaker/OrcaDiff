#!/usr/bin/env python3
"""
clean.py — Extracts Orca Slicer CONFIG_BLOCK parameters from .gcode files.

Usage:
    python clean.py                    # interactive: lists source/ files and asks
    python clean.py <ref> <tocompare>  # non-interactive: pass files directly

Accepted input formats: .gcode  |  .gcode.ref  |  .gcode.tocompare
Output in cleaned/: <stem>.gcode.ref  and  <stem>.gcode.tocompare
"""

import sys
from pathlib import Path

GCODE_SUFFIXES = (".gcode", ".gcode.ref", ".gcode.tocompare")


def extract_config_block(path: Path) -> list[str]:
    lines = []
    in_block = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if "; CONFIG_BLOCK_START" in line:
                in_block = True
            if in_block:
                lines.append(line)
            if "; CONFIG_BLOCK_END" in line:
                break
    return lines


def base_stem(path: Path) -> str:
    name = path.name
    for suffix in (".ref", ".tocompare"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def find_source_files(source_dir: Path) -> list[Path]:
    files = []
    for suffix in GCODE_SUFFIXES:
        files.extend(source_dir.glob(f"*{suffix}"))
    seen, unique = set(), []
    for f in sorted(files):
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def pick(prompt: str, files: list[Path]) -> Path:
    while True:
        raw = input(f"{prompt} [1-{len(files)}]: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(files):
            return files[int(raw) - 1]
        print(f"  → enter a number between 1 and {len(files)}")


def interactive(source_dir: Path) -> tuple[Path, Path]:
    files = find_source_files(source_dir)
    if not files:
        print(f"No gcode files found in {source_dir}/")
        sys.exit(1)

    print(f"\nFiles found in {source_dir}/:")
    for i, f in enumerate(files, 1):
        print(f"  [{i}] {f.name}")
    print()

    ref = pick("Which is the REFERENCE (good settings)?    ", files)
    cmp = pick("Which is the file TO COMPARE (problematic)?", files)

    if ref == cmp:
        print("Error: both files are the same.")
        sys.exit(1)

    return ref, cmp


def process(ref_path: Path, cmp_path: Path) -> None:
    for p in (ref_path, cmp_path):
        if not p.exists():
            print(f"Error: file not found: {p}")
            sys.exit(1)

    out_dir = Path("cleaned")
    out_dir.mkdir(exist_ok=True)

    ref_out = out_dir / (base_stem(ref_path) + ".ref")
    cmp_out = out_dir / (base_stem(cmp_path) + ".tocompare")

    ref_lines = extract_config_block(ref_path)
    cmp_lines = extract_config_block(cmp_path)

    if not ref_lines:
        print(f"Warning: no CONFIG_BLOCK found in {ref_path}")
    if not cmp_lines:
        print(f"Warning: no CONFIG_BLOCK found in {cmp_path}")

    ref_out.write_text("\n".join(ref_lines), encoding="utf-8")
    cmp_out.write_text("\n".join(cmp_lines), encoding="utf-8")

    print(f"\nref        → {ref_out}  ({len(ref_lines)} lines)")
    print(f"tocompare  → {cmp_out}  ({len(cmp_lines)} lines)")


def main():
    if len(sys.argv) == 1:
        source_dir = Path("source")
        if not source_dir.exists():
            source_dir.mkdir()
            Path("cleaned").mkdir(exist_ok=True)
            print(f"Created source/ and cleaned/")
            print(f"Place your .gcode files in source/ then run again.")
            sys.exit(0)
        ref_path, cmp_path = interactive(source_dir)
    elif len(sys.argv) == 3:
        ref_path, cmp_path = Path(sys.argv[1]), Path(sys.argv[2])
    else:
        print("Usage: python clean.py [<ref> <tocompare>]")
        sys.exit(1)

    process(ref_path, cmp_path)


if __name__ == "__main__":
    main()
