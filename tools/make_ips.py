#!/usr/bin/env python3
"""Create a guarded IPS patch from a JSON list of byte replacements.

This tool only emits a patch; it never edits the source ROM. It refuses to run
unless the base SHA-256 and every expected original byte sequence match.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_hex(value: str, field: str) -> bytes:
    try:
        return bytes.fromhex(value.replace(" ", "").replace("\n", ""))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid hexadecimal byte string") from exc


def build_records(rom: bytes, spec: dict) -> list[tuple[int, bytes]]:
    expected_hash = spec.get("base_sha256", "").lower()
    actual_hash = sha256(rom)
    if not expected_hash or actual_hash != expected_hash:
        raise ValueError(f"Base SHA-256 mismatch: expected {expected_hash or '(missing)'}, got {actual_hash}")
    target_size = spec.get("target_size", len(rom))
    if target_size != len(rom):
        raise ValueError(f"Target size mismatch: spec={target_size}, ROM={len(rom)}")
    patches = spec.get("patches")
    if not isinstance(patches, list) or not patches:
        raise ValueError("spec must contain a non-empty 'patches' list")
    records: list[tuple[int, bytes]] = []
    occupied: list[tuple[int, int]] = []
    for i, item in enumerate(patches):
        try:
            offset_raw = item["offset"]
            offset = int(offset_raw, 0) if isinstance(offset_raw, str) else int(offset_raw)
            expected = parse_hex(item["expected_hex"], f"patches[{i}].expected_hex")
            replacement = parse_hex(item["replacement_hex"], f"patches[{i}].replacement_hex")
        except (KeyError, TypeError) as exc:
            raise ValueError(f"patches[{i}] requires offset, expected_hex, and replacement_hex") from exc
        if not expected or not replacement:
            raise ValueError(f"patches[{i}] cannot have empty byte sequences")
        if len(expected) != len(replacement):
            raise ValueError(f"patches[{i}] replacement must be the same length as expected bytes")
        end = offset + len(expected)
        if offset < 0 or end > len(rom):
            raise ValueError(f"patches[{i}] range 0x{offset:X}..0x{end:X} is outside the ROM")
        for old_start, old_end in occupied:
            if offset < old_end and old_start < end:
                raise ValueError(f"patches[{i}] overlaps another patch range")
        actual = rom[offset:end]
        if actual != expected:
            raise ValueError(
                f"patches[{i}] original bytes mismatch at 0x{offset:X}: "
                f"expected {expected.hex().upper()}, got {actual.hex().upper()}"
            )
        occupied.append((offset, end))
        records.append((offset, replacement))
    records.sort(key=lambda pair: pair[0])
    return records


def encode_ips(records: list[tuple[int, bytes]]) -> bytes:
    out = bytearray(b"PATCH")
    for offset, payload in records:
        if not 0 <= offset <= 0xFFFFFF:
            raise ValueError(f"IPS offset outside 24-bit range: 0x{offset:X}")
        if not 1 <= len(payload) <= 0xFFFF:
            raise ValueError("IPS record payload length must be 1..65535 bytes")
        out.extend(offset.to_bytes(3, "big"))
        out.extend(len(payload).to_bytes(2, "big"))
        out.extend(payload)
    out.extend(b"EOF")
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("spec", type=Path, help="JSON patch specification")
    parser.add_argument("output", type=Path, help="output .ips path")
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    records = build_records(rom, spec)
    patch = encode_ips(records)
    args.output.write_bytes(patch)
    print(f"Wrote {args.output} ({len(patch)} bytes, {len(records)} guarded records)")
    print(f"Base ROM SHA-256: {sha256(rom)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
