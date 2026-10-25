import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from snes_rom import find_fill_runs, lorom_address, lorom_offset, parse_header, sha256_bytes
from make_ips import build_records, encode_ips


class SnesRomTests(unittest.TestCase):
    def test_lorom_round_trip_examples(self):
        for offset in (0x000006, 0x009018, 0x1F8072, 0x1F1806):
            bank, address = lorom_address(offset)
            self.assertEqual(lorom_offset(bank, address), offset)

    def test_lorom_rejects_non_rom_window(self):
        with self.assertRaises(ValueError):
            lorom_offset(0x7E, 0x8000)
        with self.assertRaises(ValueError):
            lorom_offset(0x80, 0x7FFF)

    def test_fill_runs(self):
        data = b"\x00" + b"\xFF" * 5 + b"\x01" + b"\xFF" * 3
        self.assertEqual(find_fill_runs(data, 0xFF, 4), [(1, 6)])

    def test_header_parse_and_checksum_pair(self):
        data = bytearray(0x8000)
        header = 0x7FC0
        data[header:header + 21] = b"TEST ROM             "
        data[header + 0x15] = 0x30
        data[header + 0x18] = 0
        data[header + 0x19] = 6
        data[header + 0x1C:header + 0x1E] = (0x1234).to_bytes(2, "little")
        data[header + 0x1E:header + 0x20] = (0xEDCB).to_bytes(2, "little")
        data[0x7FFC:0x7FFE] = (0xFFA7).to_bytes(2, "little")
        parsed = parse_header(bytes(data))
        self.assertEqual(parsed.title, "TEST ROM")
        self.assertTrue(parsed.checksum_pair_valid)
        self.assertEqual(parsed.sram_size_code, 0)
        self.assertEqual(parsed.region_name, "France/Europe")


class IpsTests(unittest.TestCase):
    def test_guarded_ips_record(self):
        rom = b"\x00\x01\x02\x03\x04"
        spec = {
            "base_sha256": sha256_bytes(rom),
            "target_size": len(rom),
            "patches": [{
                "offset": "0x01",
                "expected_hex": "0102",
                "replacement_hex": "AABB",
            }],
        }
        records = build_records(rom, spec)
        self.assertEqual(encode_ips(records), b"PATCH\x00\x00\x01\x00\x02\xAA\xBBEOF")

    def test_ips_rejects_hash_mismatch(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            build_records(b"abc", {"base_sha256": "wrong", "patches": []})

    def test_ips_rejects_overlap(self):
        rom = b"\x00" * 8
        spec = {
            "base_sha256": sha256_bytes(rom),
            "target_size": len(rom),
            "patches": [
                {"offset": 1, "expected_hex": "0000", "replacement_hex": "0101"},
                {"offset": 2, "expected_hex": "0000", "replacement_hex": "0202"},
            ],
        }
        with self.assertRaisesRegex(ValueError, "overlaps"):
            build_records(rom, spec)


if __name__ == "__main__":
    unittest.main()
