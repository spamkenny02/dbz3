#!/usr/bin/env python3
"""Compare two ROM files without writing to either input."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from snes_rom import load_rom, sha256_bytes


def diff_runs(a: bytes, b: bytes) -> list[dict[str, int]]:
    if len(a) != len(b):
        raise ValueError(f"ROM sizes differ: {len(a)} vs {len(b)}")
    runs: list[dict[str, int]] = []
    start: int | None = None
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            if start is None:
                start = i
        elif start is not None:
            runs.append({"start": start, "end_exclusive": i, "length": i - start})
            start = None
    if start is not None:
        runs.append({"start": start, "end_exclusive": len(a), "length": len(a) - start})
    return runs


def equal_runs(a: bytes, b: bytes, min_length: int) -> list[dict[str, int]]:
    if len(a) != len(b):
        raise ValueError(f"ROM sizes differ: {len(a)} vs {len(b)}")
    runs: list[dict[str, int]] = []
    start: int | None = None
    for i, (x, y) in enumerate(zip(a, b)):
        if x == y:
            if start is None:
                start = i
        elif start is not None:
            if i - start >= min_length:
                runs.append({"start": start, "end_exclusive": i, "length": i - start})
            start = None
    if start is not None and len(a) - start >= min_length:
        runs.append({"start": start, "end_exclusive": len(a), "length": len(a) - start})
    return runs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom_a", type=Path)
    parser.add_argument("rom_b", type=Path)
    parser.add_argument("--min-run", type=lambda x: int(x, 0), default=0x100,
                        help="minimum run length for reported identical ranges (default: 0x100)")
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()
    a, b = load_rom(args.rom_a), load_rom(args.rom_b)
    if len(a) != len(b):
        parser.error(f"ROM sizes differ ({len(a)} vs {len(b)}); comparison expects equal sizes")
    diffs = diff_runs(a, b)
    equals = equal_runs(a, b, args.min_run)
    report = {
        "rom_a": {"file": args.rom_a.name, "size_bytes": len(a), "sha256": sha256_bytes(a)},
        "rom_b": {"file": args.rom_b.name, "size_bytes": len(b), "sha256": sha256_bytes(b)},
        "identical": a == b,
        "differing_byte_count": sum(run["length"] for run in diffs),
        "differing_run_count": len(diffs),
        "differing_runs": diffs,
        "identical_runs_min_length": args.min_run,
        "identical_run_count": len(equals),
        "identical_runs": equals,
    }
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
