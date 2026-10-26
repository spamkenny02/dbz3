#!/usr/bin/env python3
"""Read-only preflight for the French Ultime Menace Story Mode integration.

The verifier checks a specific known ROM revision and selected static-analysis
hooks. It does not modify the ROM and does not prove runtime safety or that an
FF-filled range is unused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA256 = "663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa"
ROM_SIZE = 0x200000

# Exact fresh-boot-to-selector and confirmation bytes in the supplied ROM.
HOOKS = {
    "start_to_submode2": (0x1F9A47, bytes.fromhex("A9 02 8D 78 18 A9 00 8D 79 18")),
    "submode2_setup": (0x1F8104, bytes.fromhex("A9 0C 85 23 22 6D 82 BF 22 FA 85 BF 22 4B 87 BF")),
    "selector_input_gate": (0x1FAA8F, bytes.fromhex("E2 20 AD A0 18 D0 03 4C 48 AB")),
    "cursor_up_wrap": (0x1FAB92, bytes.fromhex("A9 02")),
    "cursor_down_limit": (0x1FABB1, bytes.fromhex("C9 02")),
    "selection_confirmation_store": (0x1FAAF6, bytes.fromhex("AD 6C 19 8D 8C 18")),
    "submode5_assignment": (0x1FAB18, bytes.fromhex("A9 05 8D 78 18")),
    "return_to_state_dispatcher": (0x1FAB32, bytes.fromhex("5C 7A 80 80")),
}

INIT_TABLE_OFFSET = 0x00F9
FRAME_TABLE_OFFSET = 0x02E3
INIT_POINTERS = [
    0x819018, 0x87DD17, 0x80811D, 0x80811D, 0x81C2F9,
    0x80811D, 0xBF8072, 0x80811D, 0x80811D, 0x80811D, 0x80811D,
    0x81915B,  # special alternate initializer at global-state index 11
]
FRAME_POINTERS = [
    0x819592, 0x87DDC9, 0x808304, 0x808304, 0x81C3D8,
    0x808304, 0xBF9AD3, 0x808304, 0x808304, 0x808304, 0x808304,
]
FILL_START = 0x1F1806
FILL_END = 0x1F8000  # end-exclusive; maps to the next LoROM bank boundary


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_u24(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 3 > len(data):
        raise ValueError("24-bit pointer is outside the ROM")
    return int.from_bytes(data[offset:offset + 3], "little")


def read_pointer_table(data: bytes, offset: int, count: int) -> list[int]:
    return [read_u24(data, offset + 3 * i) for i in range(count)]


def verify_rom(data: bytes, strict_hash: bool = True) -> dict:
    digest = sha256(data)
    if strict_hash and digest != EXPECTED_SHA256:
        raise ValueError(
            "ROM SHA-256 mismatch; this preflight is for the exact supplied French revision. "
            f"Expected {EXPECTED_SHA256}, got {digest}"
        )
    if len(data) != ROM_SIZE:
        raise ValueError(f"Expected a 2 MiB ROM ({ROM_SIZE} bytes), got {len(data)}")

    hook_results = {}
    for name, (offset, expected) in HOOKS.items():
        actual = data[offset:offset + len(expected)]
        hook_results[name] = {
            "offset": f"0x{offset:06X}",
            "expected": expected.hex(" ").upper(),
            "actual": actual.hex(" ").upper(),
            "matches": actual == expected,
        }

    init_ptrs = read_pointer_table(data, INIT_TABLE_OFFSET, len(INIT_POINTERS))
    frame_ptrs = read_pointer_table(data, FRAME_TABLE_OFFSET, len(FRAME_POINTERS))
    init_matches = init_ptrs == INIT_POINTERS
    frame_matches = frame_ptrs == FRAME_POINTERS
    fill_is_ff = data[FILL_START:FILL_END] == b"\xFF" * (FILL_END - FILL_START)

    header = data[0x7FC0:0x7FE0]
    title = header[:21].decode("ascii", errors="replace").rstrip(" \x00\xFF")
    sram_code = header[0x18]
    return {
        "file_size": len(data),
        "sha256": digest,
        "internal_title": title,
        "sram_size_code": sram_code,
        "sram_declared": sram_code != 0,
        "hooks": hook_results,
        "init_table": {
            "offset": f"0x{INIT_TABLE_OFFSET:06X}",
            "count": len(init_ptrs),
            "matches_recorded_layout": init_matches,
            "pointers": [f"0x{x:06X}" for x in init_ptrs],
        },
        "frame_table": {
            "offset": f"0x{FRAME_TABLE_OFFSET:06X}",
            "count": len(frame_ptrs),
            "matches_recorded_layout": frame_matches,
            "pointers": [f"0x{x:06X}" for x in frame_ptrs],
        },
        "candidate_fill_region": {
            "start": f"0x{FILL_START:06X}",
            "end_exclusive": f"0x{FILL_END:06X}",
            "length": FILL_END - FILL_START,
            "all_ff": fill_is_ff,
            "known_code_references": ["81:D561 uses LDA.l,X targeting BE:9806", "81:D590 uses LDA.l,X targeting BE:9806"],
            "warning": "This FF-filled range has existing code references and must not be overwritten. The prototype uses expanded LoROM banks C0-FF instead.",
        },
        "all_checks_match": (
            all(x["matches"] for x in hook_results.values())
            and init_matches and frame_matches and fill_is_ff
            and title == "DRAGONBALL Z3" and sram_code == 0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--json", type=Path, help="also write the report to this JSON file")
    parser.add_argument("--allow-hash-mismatch", action="store_true", help="diagnose a different 2 MiB image without claiming it is the known revision")
    args = parser.parse_args()
    report = verify_rom(args.rom.read_bytes(), strict_hash=not args.allow_hash_mismatch)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json:
        args.json.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["all_checks_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
