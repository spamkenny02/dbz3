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

class ProgressiveTextTests(unittest.TestCase):
    def test_hidden_glyph_keeps_background_then_reveals_final_tiles(self):
        from PIL import Image
        from story_graphics import reveal_image,decode
        background=Image.new('RGB',(256,224),(0,0,255));background.putpixel((24,152),(255,0,0))
        complete=background.copy();complete.putpixel((24,152),(255,255,255))
        result=reveal_image(background,complete,[(24,152)])
        self.assertEqual(decode(result['tiles'],result['tilemap'],result['cgram']).tobytes(),background.tobytes())
        final=bytearray(result['tilemap'])
        for off,top,bottom in result['reveals']:
            final[off:off+2]=top.to_bytes(2,'little');final[off+64:off+66]=bottom.to_bytes(2,'little')
        self.assertEqual(bytes(final),result['final_map'])
        self.assertEqual(decode(result['tiles'],final,result['cgram']).tobytes(),complete.tobytes())
    def test_native_ponctuation_is_not_bracket_halves(self):
        self.assertEqual(FONT_MAP['.'],0x52);self.assertEqual(FONT_MAP[','],0x54);self.assertEqual(FONT_MAP["'"],0x56)
