"""Dependency-free helpers for inspecting SNES ROM images.

This module deliberately does not modify ROM images.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass(frozen=True)
class Header:
    offset: int
    title: str
    map_mode: int
    cartridge_type: int
    rom_size_code: int
    sram_size_code: int
    region_code: int
    developer_code: int
    version: int
    checksum_complement: int
    checksum: int
    reset_vector: int

    @property
    def checksum_pair_valid(self) -> bool:
        return ((self.checksum_complement ^ self.checksum) & 0xFFFF) == 0xFFFF

    @property
    def map_mode_name(self) -> str:
        modes = {
            0x20: "LoROM", 0x21: "HiROM",
            0x30: "LoROM + FastROM", 0x31: "HiROM + FastROM",
            0x35: "ExHiROM (variant)",
        }
        return modes.get(self.map_mode, "unknown / needs manual interpretation")

    @property
    def region_name(self) -> str:
        return {
            0: "Japan", 1: "USA/NTSC", 2: "Europe/PAL", 3: "Sweden/Europe",
            4: "Finland/Europe", 5: "Denmark/Europe", 6: "France/Europe",
            7: "Netherlands/Europe", 8: "Spain/Europe", 9: "Germany/Europe",
            10: "Italy/Europe", 11: "China", 12: "Indonesia",
            13: "South Korea", 14: "International", 15: "Canada/NTSC",
            16: "Brazil/PAL-M", 17: "Australia/PAL",
        }.get(self.region_code, f"unknown ({self.region_code})")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_rom(path: str | Path) -> bytes:
    data = Path(path).read_bytes()
    if len(data) < 0x8000:
        raise ValueError(f"File is too small to be a normal SNES ROM: {len(data)} bytes")
    return data


def parse_header(data: bytes, offset: int = 0x7FC0) -> Header:
    """Parse the standard 32-byte SNES header at a candidate LoROM header offset."""
    if offset < 0 or offset + 0x20 > len(data):
        raise ValueError(f"Header at 0x{offset:X} is outside the file")
    raw = data[offset:offset + 0x20]
    title = raw[0:21].decode("ascii", errors="replace").rstrip(" \x00\xff")
    return Header(
        offset=offset,
        title=title,
        map_mode=raw[0x15],
        cartridge_type=raw[0x16],
        rom_size_code=raw[0x17],
        sram_size_code=raw[0x18],
        region_code=raw[0x19],
        developer_code=raw[0x1A],
        version=raw[0x1B],
        checksum_complement=int.from_bytes(raw[0x1C:0x1E], "little"),
        checksum=int.from_bytes(raw[0x1E:0x20], "little"),
        reset_vector=int.from_bytes(data[0x7FFC:0x7FFE], "little"),
    )


def lorom_offset(bank: int, address: int) -> int:
    """Convert a LoROM CPU address to file offset for ROM-mapped addresses.

    Supports ROM windows at addresses 8000-FFFF. This is a mapping helper,
    not a full SNES bus emulator; WRAM/IO windows are rejected.
    """
    if not (0 <= bank <= 0xFF and 0 <= address <= 0xFFFF):
        raise ValueError("bank and address must be 8-bit and 16-bit values")
    if address < 0x8000:
        raise ValueError(f"{bank:02X}:{address:04X} is not a standard LoROM ROM window")
    if 0x7E <= bank <= 0x7F:
        raise ValueError(f"{bank:02X}:{address:04X} is WRAM, not ROM")
    return ((bank & 0x7F) * 0x8000) + (address & 0x7FFF)


def lorom_address(offset: int) -> tuple[int, int]:
    """Convert a file offset to a canonical LoROM CPU address (up to 4 MiB)."""
    if offset < 0:
        raise ValueError("offset cannot be negative")
    bank_index, in_bank = divmod(offset, 0x8000)
    if bank_index >= 0x80:
        raise ValueError("offset is beyond the canonical 4 MiB LoROM mapping")
    return 0x80 + bank_index, 0x8000 + in_bank


def find_fill_runs(data: bytes, fill_byte: int = 0xFF, min_length: int = 0x1000) -> list[tuple[int, int]]:
    """Return (start, end_exclusive) runs of fill_byte at least min_length long."""
    if not 0 <= fill_byte <= 0xFF:
        raise ValueError("fill_byte must be in 0..255")
    if min_length < 1:
        raise ValueError("min_length must be positive")
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for i, value in enumerate(data):
        if value == fill_byte:
            if start is None:
                start = i
        elif start is not None:
            if i - start >= min_length:
                runs.append((start, i))
            start = None
    if start is not None and len(data) - start >= min_length:
        runs.append((start, len(data)))
    return runs
