import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from verify_story_hooks import (
    EXPECTED_SHA256,
    FRAME_POINTERS,
    FRAME_TABLE_OFFSET,
    HOOKS,
    INIT_POINTERS,
    INIT_TABLE_OFFSET,
    read_pointer_table,
    read_u24,
    verify_rom,
)


class StoryHookVerifierTests(unittest.TestCase):
    def test_read_u24_little_endian(self):
        self.assertEqual(read_u24(b"\x17\xDD\x87", 0), 0x87DD17)

    def test_read_u24_bounds(self):
        with self.assertRaises(ValueError):
            read_u24(b"\x01\x02", 0)

    def test_pointer_table(self):
        raw = b"\x18\x90\x81\x17\xDD\x87"
        self.assertEqual(read_pointer_table(raw, 0, 2), [0x819018, 0x87DD17])

    def test_known_hook_offsets_are_non_overlapping(self):
        ranges = sorted((off, off + len(expected), name) for name, (off, expected) in HOOKS.items())
        for (_, end_a, name_a), (start_b, _, name_b) in zip(ranges, ranges[1:]):
            self.assertLessEqual(end_a, start_b, f"overlapping hooks: {name_a} / {name_b}")

    def test_wrong_size_rejected(self):
        with self.assertRaisesRegex(ValueError, "Expected a 2 MiB ROM"):
            verify_rom(b"\x00" * 32, strict_hash=False)

    def test_strict_hash_rejected_before_claiming_known_revision(self):
        fake = bytearray(0x200000)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify_rom(bytes(fake), strict_hash=True)

    def test_recorded_tables_have_expected_lengths(self):
        self.assertEqual(len(INIT_POINTERS), 11)
        self.assertEqual(len(FRAME_POINTERS), 11)
        self.assertEqual(INIT_TABLE_OFFSET, 0xF9)
        self.assertEqual(FRAME_TABLE_OFFSET, 0x2E3)
        self.assertEqual(len(EXPECTED_SHA256), 64)


if __name__ == "__main__":
    unittest.main()
