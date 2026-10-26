import sys,unittest,tempfile,json,random
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from story_graphics import encode,decode,rgb555,rgb8,Payloads,page_image
from build_story_campaign import compile_campaign
from model import Assets,scene,project

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

class CampaignGraphicsTests(unittest.TestCase):
    def rom(self):
        rom=bytearray(0x400000);rom[0x7a:0x80]=bytes.fromhex('e2 20 a2 fe 1f 9a');return rom
    def test_selected_graphics_cannot_be_silently_ignored(self):
        data=project();data['scenes'][0]['background']='forest'
        with self.assertRaisesRegex(ValueError,'catalogue'):compile_campaign(data,self.rom())
    def test_background_changes_the_rom_and_metrics(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'catalog.json').write_text(json.dumps({'assets':[dict(id='forest',kind='background',path='bg.png')]}))
            data=project();s=data['scenes'][0];s.update(background='forest',kind='ending',dialogue='BONJOUR')
            hashes=[]
            for color in ('red','blue'):
                Image.new('RGB',(256,224),color).save(root/'bg.png');rom=self.rom();report=compile_campaign(data,rom,Assets(root/'catalog.json'))
                self.assertTrue(report['graphics_compiled']);self.assertEqual(report['graphic_variants'],1)
                self.assertFalse(report['graphic_metrics'][0]['quantized']);hashes.append(report['graphic_metrics'][0]['expected_rgb555_sha256'])
            self.assertNotEqual(*hashes)
    def test_large_tile_set_is_split_into_two_dma_segments(self):
        rng=random.Random(5);im=Image.new('RGB',(256,224));im.putdata([rng.choice([(255,0,0),(0,255,0),(0,0,255)]) for _ in range(256*224)])
        encoded=encode(im);self.assertGreater(encoded['metrics']['tiles'],512)
        payload=Payloads().image(encoded);self.assertEqual(len(payload['segments']),2)
        self.assertEqual(payload['segments'][1][2],0x4000)
