import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_story_prototype import (
    CODE_CPU_START, CODE_ROM_START, FONT_OFFSET, MAP_OFFSETS, PATCH_END, PATCH_START,
    STORY_CURSOR, STORY_PAGE, STORY_ROUTE, assemble_code, make_font, make_ips, make_maps,
)


class StoryPrototypeAssetsTests(unittest.TestCase):
    def test_font_is_64_snes_2bpp_tiles(self):
        self.assertEqual(len(make_font()), 64 * 16)

    def test_every_map_is_a_full_32_by_32_tilemap(self):
        maps = make_maps()
        self.assertEqual(set(maps), set(MAP_OFFSETS))
        self.assertTrue(all(len(data) == 0x800 for data in maps.values()))

    def test_menu_maps_have_four_distinct_selection_states(self):
        maps = make_maps()
        menu_maps = [maps[f"menu_{i}"] for i in range(4)]
        self.assertEqual(len(set(menu_maps)), 4)
        self.assertTrue(all(len(m) == 0x800 for m in menu_maps))

    def test_story_contains_two_routes_and_two_endings(self):
        maps = make_maps()
        self.assertNotEqual(maps["choice_gohan"], maps["choice_vegeta"])
        self.assertNotEqual(maps["ending_gohan"], maps["ending_vegeta"])

    def test_code_assembles_with_all_short_branches_in_range(self):
        code, labels = assemble_code()
        self.assertEqual(len(code), 1093)
        self.assertEqual(hashlib.sha256(code).hexdigest(), "23c35d2c59c1978c74bc898b4ee9e1cbd21cc849f6c5ca98751e4fb633d81e56")
        self.assertLess(CODE_ROM_START + len(code), FONT_OFFSET)
        expected_labels = {
            "StoryInit": 0x8054, "StoryFrame": 0x806C, "MenuInit": 0x814C,
            "MenuFrame": 0x816A, "DrawScreen": 0x822A,
            "NativeMenuAddStory": 0x8337, "StorySelectState": 0x846E,
            "StoryReturnToNativeMenu": 0x8483,
        }
        for name, address in expected_labels.items():
            self.assertEqual(labels[name], address)
        self.assertLess(PATCH_START, CODE_ROM_START)
        self.assertLess(FONT_OFFSET, PATCH_END)

    def test_native_menu_overlay_writes_eight_original_font_glyphs(self):
        code, labels = assemble_code()
        start = labels["NativeMenuAddStory"] - CODE_CPU_START
        end = labels["StorySelectState"] - CODE_CPU_START
        overlay = code[start:end]
        self.assertEqual(overlay.count(bytes.fromhex("9F 00 60 7E")), 32)
        expected_top = [
            0x2F02, 0x2F03, 0x2F04, 0x2F05, 0x2F28, 0x2F29, 0x2F2A, 0x2F2B,
            0x2F20, 0x2F21, 0x2F04, 0x2F05, 0x2F26, 0x2F27, 0x2EEC, 0x2EED,
        ]
        expected_bottom = [
            0x2F12, 0x2F13, 0x2F14, 0x2F15, 0x2F38, 0x2F39, 0x2F3A, 0x2F3B,
            0x2F30, 0x2F31, 0x2F14, 0x2F15, 0x2F36, 0x2F37, 0x2EFC, 0x2EFD,
        ]
        for value in expected_top + expected_bottom:
            needle = bytes((0xA9, value & 0xFF, value >> 8, 0x9F, 0x00, 0x60, 0x7E, 0xE8, 0xE8))
            self.assertIn(needle, overlay)

    def test_story_ram_variables_are_distinct(self):
        self.assertEqual(len({STORY_CURSOR, STORY_PAGE, STORY_ROUTE}), 3)


class IpsTests(unittest.TestCase):
    def apply_ips(self, base, patch):
        restored = bytearray(base)
        pos = 5
        while patch[pos:pos + 3] != b"EOF":
            offset = int.from_bytes(patch[pos:pos + 3], "big")
            length = int.from_bytes(patch[pos + 3:pos + 5], "big")
            pos += 5
            if offset + length > len(restored):
                restored.extend(b"\x00" * (offset + length - len(restored)))
            restored[offset:offset + length] = patch[pos:pos + length]
            pos += length
        return bytes(restored)

    def test_ips_round_trip_small_sample(self):
        base = bytes(range(32))
        changed = bytearray(base)
        changed[3:6] = b"ABC"
        changed[20] = 0xEE
        patch = make_ips(base, bytes(changed))
        self.assertTrue(patch.startswith(b"PATCH"))
        self.assertTrue(patch.endswith(b"EOF"))
        self.assertEqual(self.apply_ips(base, patch), bytes(changed))

    def test_ips_round_trip_expanded_rom(self):
        base = bytes(range(32))
        changed = bytearray(base + bytes(32))
        changed[40:43] = b"XYZ"
        patch = make_ips(base, bytes(changed))
        self.assertEqual(self.apply_ips(base, patch), bytes(changed))
        self.assertEqual(len(self.apply_ips(base, patch)), 64)


if __name__ == "__main__":
    unittest.main()
