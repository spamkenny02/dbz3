import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from sb2_style import decompress,NativeFont,FONT_MAP

class SB2StyleTests(unittest.TestCase):
    def test_literal_and_overlapping_back_reference(self):
        self.assertEqual(decompress(bytes.fromhex('06 00 07 61 62 63 30 00'),0),b'abcabc')
        self.assertEqual(decompress(bytes.fromhex('03 00 00 10 00'),0),bytes(3))
    def test_font_keeps_native_french_codepoints(self):
        self.assertEqual(FONT_MAP['O'],0x1de);self.assertEqual(FONT_MAP['u'],0xf4)
        self.assertIn('î',FONT_MAP);self.assertIn('é',FONT_MAP)
        self.assertNotEqual(FONT_MAP['é'],FONT_MAP['e'])
    def test_unknown_glyph_is_not_silently_dropped(self):
        with self.assertRaises(ValueError):NativeFont(bytes(16384)).glyph('♥')
    def test_native_glyph_layout(self):
        raw=bytearray(16384);k=FONT_MAP['A'];top=(k//16*32+k%16)*16;raw[top]=128
        g=NativeFont(raw).glyph('A');self.assertEqual(g.getpixel((0,0)),(213,222,238,255));self.assertEqual(g.getpixel((1,0))[3],0)
