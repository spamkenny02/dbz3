#!/usr/bin/env python3
"""Verify selected static-analysis claims against the exact French Ultime Menace ROM.

This is a read-only byte-level check, not a 65816 emulator or proof that fill
regions are safe to overwrite. It intentionally fails on a different ROM hash.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from snes_rom import load_rom, parse_header, sha256_bytes

EXPECTED_SHA256 = "663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa"
STATE_INIT_OFFSET = 0x00F9
FRAME_TABLE_OFFSET = 0x02E3
STATE6_INIT_TABLE_OFFSET = 0x1F80BC
STATE6_FRAME_TABLE_OFFSET = 0x1F9ADF
SELECTOR_UP_WRAP_OFFSET = 0x1FAB92
SELECTOR_DOWN_COMPARE_OFFSET = 0x1FABB1
CANDIDATE_FILL_START = 0x1F1806
CANDIDATE_FILL_END = 0x1F8000

EXPECTED_STATE_INIT = [0x819018, 0x87DD17, 0x80811D, 0x80811D, 0x81C2F9, 0x80811D, 0xBF8072]
EXPECTED_FRAME_HANDLERS = [0x819592, 0x87DDC9, 0x808304, 0x808304, 0x81C3D8, 0x808304, 0xBF9AD3]
EXPECTED_STATE6_INIT = [0xBF80D7, 0xBF80E4, 0xBF8104, 0xBF8116, 0xBF8128, 0xBF813A, 0xBF8144, 0xBF815D, 0xBF8167]
EXPECTED_STATE6_FRAME = [0x9B02, 0x9B9D, 0x9BF8, 0x9C68, 0x9CBF, 0x9B01, 0x9D02, 0x9D31, 0x9E5B, 0xA03A, 0xA03A, 0xA647, 0xA96B, 0xB0A2, 0xBA77, 0xBF89, 0xD0CC]


def read_u24(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 3], "little")


def verify(data: bytes) -> list[str]:
    problems: list[str] = []
    digest = sha256_bytes(data)
    if digest != EXPECTED_SHA256:
        raise ValueError(f"ROM SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}")
    header = parse_header(data)
    if header.title != "DRAGONBALL Z3":
        problems.append(f"Unexpected internal title: {header.title!r}")
    if header.sram_size_code != 0:
        problems.append(f"Expected SRAM size code 0, got {header.sram_size_code}")

    state_init = [read_u24(data, STATE_INIT_OFFSET + 3 * i) for i in range(len(EXPECTED_STATE_INIT))]
    if state_init != EXPECTED_STATE_INIT:
        problems.append(f"Global state initializer table mismatch: {[hex(x) for x in state_init]}")

    frame_handlers = [read_u24(data, FRAME_TABLE_OFFSET + 3 * i) for i in range(len(EXPECTED_FRAME_HANDLERS))]
    if frame_handlers != EXPECTED_FRAME_HANDLERS:
        problems.append(f"Global frame-handler table mismatch: {[hex(x) for x in frame_handlers]}")

    state6_init = [read_u24(data, STATE6_INIT_TABLE_OFFSET + 3 * i) for i in range(len(EXPECTED_STATE6_INIT))]
    if state6_init != EXPECTED_STATE6_INIT:
        problems.append(f"State-6 initializer table mismatch: {[hex(x) for x in state6_init]}")

    # These are 16-bit addresses within bank BF.
    state6_frame = [
        0xBF0000 | int.from_bytes(data[STATE6_FRAME_TABLE_OFFSET + 2 * i:STATE6_FRAME_TABLE_OFFSET + 2 * i + 2], "little")
        for i in range(len(EXPECTED_STATE6_FRAME))
    ]
    expected_frame = [0xBF0000 | x for x in EXPECTED_STATE6_FRAME]
    if state6_frame != expected_frame:
        problems.append(f"State-6 frame table mismatch: {[hex(x) for x in state6_frame]}")

    if data[SELECTOR_UP_WRAP_OFFSET:SELECTOR_UP_WRAP_OFFSET + 2] != bytes.fromhex("A9 02"):
        problems.append("Selector up-wrap immediate is no longer A9 02 at 0x1FAB92")
    if data[SELECTOR_DOWN_COMPARE_OFFSET:SELECTOR_DOWN_COMPARE_OFFSET + 2] != bytes.fromhex("C9 02"):
        problems.append("Selector down-limit compare is no longer C9 02 at 0x1FABB1")
    if data[CANDIDATE_FILL_START:CANDIDATE_FILL_END] != b"\xFF" * (CANDIDATE_FILL_END - CANDIDATE_FILL_START):
        problems.append("Candidate fill region 0x1F1806..0x1F8000 is no longer entirely FF")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    args = parser.parse_args()
    data = load_rom(args.rom)
    problems = verify(data)
    if problems:
        print("FAIL: one or more known-layout checks failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("PASS: ROM hash, header, state tables, selector limit bytes, and candidate FF run match the recorded static analysis.")
    print("WARNING: this does not prove the fill region is safe to overwrite or that a patch works in an emulator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
