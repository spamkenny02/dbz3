import sys,unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from story_graphics import encode,decode,rgb555,rgb8,Payloads,page_image

class GraphicTests(unittest.TestCase):
    def test_round_trip_all_bitplanes_and_palette_exact(self):
        im=Image.new('RGB',(256,224));im.putdata([rgb8((x%32)|((y%32)<<5)|(((x+y)%32)<<10)) for y in range(224) for x in range(256)])
        data=encode(im);self.assertEqual(decode(data['tiles'],data['tilemap'],data['cgram']).tobytes(),data['expected'].tobytes())
        self.assertTrue(data['metrics']['quantized'])
    def test_exact_palette_and_tile_deduplication(self):
        im=Image.new('RGB',(256,224),(0,255,0));im.putpixel((0,0),(255,0,0))
        data=encode(im);self.assertFalse(data['metrics']['quantized']);self.assertLessEqual(data['metrics']['tiles'],3)
        self.assertEqual(decode(data['tiles'],data['tilemap'],data['cgram']).tobytes(),im.tobytes())
    def test_bank_boundary_capacity_and_dedup(self):
        pool=Payloads(start=0x217ff0);ptr=pool.put(bytes(32));self.assertEqual(ptr,0xc38000)
        self.assertEqual(pool.put(bytes(32)),ptr)
        with self.assertRaises(ValueError):Payloads(start=0x3ffff0).put(bytes(32))
    def test_dialogue_ui_is_in_image(self):
        a=page_image(Image.new('RGB',(256,224),'red'),'TEST',['BONJOUR'])
        self.assertNotEqual(a.getpixel((8,166)),a.getpixel((250,166)))
