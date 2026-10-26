import sys, unittest, tempfile, subprocess, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'editor'))
from build_story_campaign import compile_campaign,ascii_text,FIGHTER_IDS,build
from model import load_project

class CampaignTests(unittest.TestCase):
    def test_graph_compiles_to_new_banks_and_guarded_transition(self):
        data=load_project(ROOT/'editor/prelude_tournoi.json')
        rom=bytearray(0x400000);rom[0x7a:0x80]=bytes.fromhex('e2 20 a2 fe 1f 9a')
        report=compile_campaign(data,rom)
        self.assertEqual(report['scenes'],17);self.assertGreaterEqual(report['pages'],17)
        self.assertLess(report['code_bytes'],0x8000)
        self.assertEqual(rom[0x7a],0x5c);self.assertEqual(rom[0x7d],0xc1)
        self.assertEqual(rom[0x200000+12*3+2],0xc1)
        self.assertEqual(rom[0x20002a+12*3+2],0xc1)
        self.assertFalse(report['graphics_compiled'])
    def test_wrong_transition_layout_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'transition signature'):
            compile_campaign(load_project(ROOT/'editor/prelude_tournoi.json'),bytearray(0x400000))
    def test_output_cannot_overwrite_source_rom(self):
        with self.assertRaisesRegex(ValueError,'paths must all differ'):
            build('same.sfc','project.json','same.sfc','out.ips','report.json')
    def test_pagination_keeps_long_dialogue(self):
        data=load_project(ROOT/'editor/prelude_tournoi.json');data['scenes'][0]['dialogue']='\n'.join(['Une longue ligne de dialogue.']*25)
        rom=bytearray(0x400000);rom[0x7a:0x80]=bytes.fromhex('e2 20 a2 fe 1f 9a')
        report=compile_campaign(data,rom);self.assertGreater(report['pages'],len(data['scenes']))
        self.assertEqual(ascii_text('Entraînement…'),'ENTRAINEMENT...')
    def test_standalone_zip_builder_imports_from_any_working_directory(self):
        archive=ROOT/'releases/Atelier_Scenario_GUI_Combats_v7.zip'
        with tempfile.TemporaryDirectory() as d:
            unpacked=Path(d)/'Atelier scénario avec espaces';unpacked.mkdir()
            with zipfile.ZipFile(archive) as z:z.extractall(unpacked)
            self.assertEqual((unpacked/'tools/build_story_campaign.py').read_bytes(),(ROOT/'tools/build_story_campaign.py').read_bytes())
            result=subprocess.run([sys.executable,str(unpacked/'tools/build_story_campaign.py'),'--help'],cwd=d,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
    def test_roster_is_native_and_not_guessed(self):
        self.assertEqual([FIGHTER_IDS[n] for n in ('Gohan','Goten','Vegeta','Trunks')],[2,3,1,4])
        self.assertNotIn('Piccolo',FIGHTER_IDS)
