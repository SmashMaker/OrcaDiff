#!/usr/bin/env python3
"""
diff.py — Pretty diff between two Orca Slicer parameter files.

Usage:
    python diff.py                                      # auto-detect from cleaned/
    python diff.py <file.gcode.tocompare> <file.gcode.ref>

Outputs:
    - terminal: coloured table
    - diff.md:  markdown table saved next to this script
"""

import sys
import os
from pathlib import Path

def _enable_ansi():
    if sys.platform == "win32":
        os.system("color")

_enable_ansi()

R   = "\033[91m"
G   = "\033[92m"
Y   = "\033[93m"
C   = "\033[96m"
B   = "\033[1m"
D   = "\033[2m"
RST = "\033[0m"

SKIP_KEYS = {"different_settings_to_system"}

def parse_params(path: Path) -> dict[str, str]:
    params: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith(";") or "=" not in line:
            continue
        content = line[1:].strip()
        key, _, value = content.partition("=")
        key = key.strip()
        if key and key not in SKIP_KEYS:
            params[key] = value.strip()
    return params


def find_files() -> tuple[Path, Path]:
    cleaned = Path("cleaned")
    if not cleaned.exists():
        cleaned.mkdir()
        print("Created cleaned/  — run clean.py first to populate it.")
        sys.exit(0)
    refs = sorted(cleaned.glob("*.gcode.ref"))
    cmps = sorted(cleaned.glob("*.gcode.tocompare"))
    if not refs or not cmps:
        print("No .gcode.ref / .gcode.tocompare found in cleaned/  — run clean.py first.")
        sys.exit(1)
    if len(refs) > 1 or len(cmps) > 1:
        print("Multiple files found — pass paths explicitly:")
        print("  python diff.py <tocompare> <ref>")
        sys.exit(1)
    return cmps[0], refs[0]


def compute_diffs(cmp_path: Path, ref_path: Path):
    cmp_params = parse_params(cmp_path)
    ref_params = parse_params(ref_path)
    all_keys = sorted(set(cmp_params) | set(ref_params))
    return [
        (k, cmp_params.get(k), ref_params.get(k))
        for k in all_keys
        if cmp_params.get(k) != ref_params.get(k)
    ]


def _trunc(s: str, width: int) -> str:
    return s if len(s) <= width else s[: width - 1] + "…"


def render_terminal(cmp_path: Path, ref_path: Path, diffs: list) -> None:
    if not diffs:
        print(f"\n{G}No differences found.{RST}\n")
        return

    MAX_VAL  = 60
    col_key  = min(max(len(k)                          for k, _, _ in diffs), 45)
    col_cmp  = min(max(len(v) if v else 8              for _, v, _ in diffs), MAX_VAL)
    col_ref  = min(max(len(v) if v else 8              for _, _, v in diffs), MAX_VAL)
    total    = col_key + col_cmp + col_ref + 10

    cmp_label = cmp_path.name.replace(".gcode.tocompare", "")
    ref_label = ref_path.name.replace(".gcode.ref", "")

    print()
    print(f"{B}{C}{'═' * total}{RST}")
    print(f"{B}{C}  Orca Slicer parameter diff{RST}")
    print(f"{B}{C}{'─' * total}{RST}")
    print(f"  {R}{B}TO COMPARE{RST}  {_trunc(cmp_label, total - 15)}")
    print(f"  {G}{B}REFERENCE {RST}  {_trunc(ref_label, total - 15)}")
    print(f"{B}{C}{'═' * total}{RST}")
    print(f"  {D}{'PARAMETER':<{col_key}}  {'TO COMPARE':<{col_cmp}}  {'REFERENCE':<{col_ref}}{RST}")
    print(f"  {C}{'─' * (total - 2)}{RST}")

    for key, cmp_val, ref_val in diffs:
        cmp_str = _trunc(cmp_val, col_cmp) if cmp_val is not None else f"{D}(absent){RST}"
        ref_str = _trunc(ref_val, col_ref) if ref_val is not None else f"{D}(absent){RST}"
        print(f"  {Y}{key:<{col_key}}{RST}  {R}{cmp_str:<{col_cmp}}{RST}  {G}{ref_str}{RST}")

    print()
    print(f"{B}{C}{'═' * total}{RST}")
    print(f"  {B}{len(diffs)} difference(s){RST}   {R}to compare (new){RST}   {G}reference (good){RST}")
    print(f"{B}{C}{'═' * total}{RST}")
    print()


def render_markdown(cmp_path: Path, ref_path: Path, diffs: list, out_path: Path) -> None:
    cmp_label = cmp_path.name.replace(".gcode.tocompare", "")
    ref_label = ref_path.name.replace(".gcode.ref", "")

    lines = [
        "# Orca Slicer — parameter diff",
        "",
        "| | File |",
        "|---|---|",
        f"| **To compare** | `{cmp_label}` |",
        f"| **Reference**  | `{ref_label}` |",
        "",
    ]

    if not diffs:
        lines.append("No differences found.")
    else:
        lines += [
            f"**{len(diffs)} difference(s)**",
            "",
            "| Parameter | To compare | Reference |",
            "|-----------|-----------|-----------|",
        ]
        for key, cmp_val, ref_val in diffs:
            cmp_str = f"`{cmp_val}`" if cmp_val is not None else "*(absent)*"
            ref_str = f"`{ref_val}`" if ref_val is not None else "*(absent)*"
            lines.append(f"| `{key}` | {cmp_str} | {ref_str} |")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  saved → {out_path}")


def main():
    if len(sys.argv) == 3:
        cmp_path = Path(sys.argv[1])
        ref_path = Path(sys.argv[2])
        for p in (cmp_path, ref_path):
            if not p.exists():
                print(f"Error: file not found: {p}")
                sys.exit(1)
    elif len(sys.argv) == 1:
        cmp_path, ref_path = find_files()
    else:
        print("Usage: python diff.py [<tocompare> <ref>]")
        sys.exit(1)

    diffs = compute_diffs(cmp_path, ref_path)

    render_terminal(cmp_path, ref_path, diffs)

    md_path = Path(__file__).parent / "diff.md"
    render_markdown(cmp_path, ref_path, diffs, md_path)


if __name__ == "__main__":
    main()
