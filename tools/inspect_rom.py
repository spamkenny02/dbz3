#!/usr/bin/env python3
"""Print a reproducible, read-only SNES ROM diagnostic report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from snes_rom import find_fill_runs, load_rom, lorom_address, parse_header, sha256_bytes


def inspect(path: Path, min_fill: int) -> dict:
    data = load_rom(path)
    header = parse_header(data)
    runs = find_fill_runs(data, 0xFF, min_fill)
    mapped_runs = []
    for start, end in runs:
        try:
            bank, address = lorom_address(start)
            cpu_start = f"{bank:02X}:{address:04X}"
        except ValueError:
            cpu_start = None
        mapped_runs.append({
            "offset_start": start,
            "offset_end_exclusive": end,
            "length": end - start,
            "cpu_start_lorom": cpu_start,
        })
    return {
        "file": path.name,
        "size_bytes": len(data),
        "sha256": sha256_bytes(data),
        "header": {
            "offset": f"0x{header.offset:X}",
            "title": header.title,
            "map_mode_byte": f"0x{header.map_mode:02X}",
            "map_mode_interpretation": header.map_mode_name,
            "cartridge_type_byte": f"0x{header.cartridge_type:02X}",
            "rom_size_code": header.rom_size_code,
            "sram_size_code": header.sram_size_code,
            "sram_declared": header.sram_size_code != 0,
            "region_code": header.region_code,
            "region_interpretation": header.region_name,
            "developer_code": header.developer_code,
            "version": header.version,
            "checksum_complement": f"0x{header.checksum_complement:04X}",
            "checksum": f"0x{header.checksum:04X}",
            "checksum_pair_valid": header.checksum_pair_valid,
            "reset_vector": f"0x{header.reset_vector:04X}",
        },
        "ff_fill_runs": mapped_runs,
        "ff_fill_run_count": len(mapped_runs),
        "ff_fill_total_bytes_in_reported_runs": sum(r["length"] for r in mapped_runs),
        "warning": "FF-filled runs are candidates only; they are not proven free until references and runtime behavior are checked.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="Path to a user-owned .sfc/.smc ROM")
    parser.add_argument("--min-fill", type=lambda x: int(x, 0), default=0x1000,
                        help="minimum FF-run length, decimal or 0x-prefixed (default: 0x1000)")
    parser.add_argument("--json", dest="json_path", type=Path,
                        help="also write the report to a JSON file")
    args = parser.parse_args()
    report = inspect(args.rom, args.min_fill)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
