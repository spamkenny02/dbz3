import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_story_prototype import (
    CODE_ROM_START, FONT_OFFSET, MAP_OFFSETS, PATCH_END, PATCH_START,
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
        self.assertEqual(len(code), 756)
        self.assertEqual(hashlib.sha256(code).hexdigest(), "24f587b2202ef507899853aae06772d36d6d7f6cac69568892bf06a52cce2c6e")
        self.assertLess(CODE_ROM_START + len(code), FONT_OFFSET)
        expected_labels = {
            "StoryInit": 0x985A, "StoryFrame": 0x9872, "MenuInit": 0x9956,
            "MenuFrame": 0x9981, "DrawScreen": 0x9A41,
        }
        for name, address in expected_labels.items():
            self.assertEqual(labels[name], address)
        self.assertLess(PATCH_START, CODE_ROM_START)
        self.assertLess(FONT_OFFSET, PATCH_END)

    def test_story_ram_variables_are_distinct(self):
        self.assertEqual(len({STORY_CURSOR, STORY_PAGE, STORY_ROUTE}), 3)


class IpsTests(unittest.TestCase):
    def test_ips_round_trip_small_sample(self):
        base = bytes(range(32))
        changed = bytearray(base)
        changed[3:6] = b"ABC"
        changed[20] = 0xEE
        patch = make_ips(base, bytes(changed))
        self.assertTrue(patch.startswith(b"PATCH"))
        self.assertTrue(patch.endswith(b"EOF"))
        restored = bytearray(base)
        pos = 5
        while patch[pos:pos + 3] != b"EOF":
            offset = int.from_bytes(patch[pos:pos + 3], "big")
            length = int.from_bytes(patch[pos + 3:pos + 5], "big")
            pos += 5
            restored[offset:offset + length] = patch[pos:pos + length]
            pos += length
        self.assertEqual(bytes(restored), bytes(changed))


if __name__ == "__main__":
    unittest.main()
