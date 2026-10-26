import json,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'editor'));sys.path.insert(0,str(ROOT/'tools'))
from model import project,scene,validate,duplicate,save_project,load_project,Assets,compose
from snes_graphics import objects,split_objects
from extract_sb2_assets import probe_rom

class SceneTests(unittest.TestCase):
    def test_routes_round_trip_and_detect_dangling_choice(self):
        data=project();second=scene('Fin');data['scenes'].append(second)
        data['scenes'][0]['choices']=[dict(label='Continuer',target=second['id'])]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'story.json';save_project(data,path);self.assertEqual(load_project(path),data)
        data['scenes'].pop();self.assertTrue(validate(data))
    def test_duplicate_does_not_share_actor_or_choice_data(self):
        s=scene();s['actors']=[dict(asset='x',x=10)];copy=duplicate(s)
        copy['actors'][0]['x']=90;self.assertEqual(s['actors'][0]['x'],10);self.assertNotEqual(s['id'],copy['id'])
    def test_layer_order_flip_and_negative_clipping(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);red=Image.new('RGBA',(2,1));red.putdata([(255,0,0,255),(0,255,0,255)]);red.save(root/'a.png')
            (root/'catalog.json').write_text(json.dumps({'assets':[dict(id='a',path='a.png')]}))
            assets=Assets(root/'catalog.json');s=scene();s['actors']=[dict(asset='a',x=-1,y=0,scale=1,flip=True,z=0)]
            self.assertEqual(compose(s,assets).getpixel((0,0)),(255,0,0,255))
            s['actors'].append(dict(asset='a',x=0,y=0,scale=1,flip=True,z=1))
            self.assertEqual(compose(s,assets).getpixel((0,0)),(0,255,0,255))
    def test_catalog_path_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'catalog.json';path.write_text(json.dumps({'assets':[dict(id='a',path='../outside.png')]}))
            with self.assertRaises(ValueError):Assets(path).image('a')
    def test_probe_is_a_copy_and_wrong_layout_rejected(self):
        raw=bytearray(b'\xff'*0x400000);raw[0x1f8474:0x1f8478]=bytes.fromhex('E2 20 A5 20')
        original=bytes(raw);out=probe_rom(original,2)
        self.assertEqual(original,bytes(raw));self.assertEqual(out[0x7fa0],5);self.assertNotEqual(out,original)
        with self.assertRaises(ValueError):probe_rom(bytes(0x400000),2)

class SpriteTests(unittest.TestCase):
    def test_4bpp_palette_zero_transparency_and_flip(self):
        v=bytearray(65536);v[0]=0x80;pal=bytearray(512);pal[258:260]=(31).to_bytes(2,'little')
        oam=bytearray(544)
        for i in range(128):oam[i*4+1]=224
        oam[:4]=bytes([4,5,0,0])
        im,_=objects(v,pal,oam,0);self.assertEqual(im.getpixel((4,5)),(255,0,0,255));self.assertEqual(im.getpixel((5,5))[3],0)
        oam[3]=0x40;im,_=objects(v,pal,oam,0);self.assertEqual(im.getpixel((11,5)),(255,0,0,255))
    def test_separate_distant_prop_and_drop_noise(self):
        im=Image.new('RGBA',(40,20))
        for x0 in (2,25):
            for x in range(x0,x0+4):
                for y in range(3,8):im.putpixel((x,y),(255,255,255,255))
        im.putpixel((15,15),(255,255,255,255));parts=split_objects(im)
        self.assertEqual(len(parts),2);self.assertEqual(parts[0][1],[2,3])

if __name__=='__main__':unittest.main()
