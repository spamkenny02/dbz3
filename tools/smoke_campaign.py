#!/usr/bin/env python3
"""Exercise the full campaign with Snes9x; inject KOs to test both return paths.
This validates battle entry/result routing, not a human-played complete match.
"""
import argparse, ctypes as C, hashlib, json, sys
from pathlib import Path
from libretro_session import Session
from build_story_campaign import FIGHTER_IDS
from story_graphics import rgb555,pixels_of
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'editor'))
from model import load_project

def run(core,rom,project,second=False,lose=False,natural=False,manifest=None):
    s=Session(core);raw=Path(rom).read_bytes();s.load(raw)
    ram=(C.c_ubyte*131072).from_address(s.lib.retro_get_memory_data(2))
    manifest=json.loads(Path(manifest).read_text()) if manifest else None
    data=load_project(project);combats=[n for n in data['scenes'] if n['kind']=='combat'];records=[]
    last=-200;active=None;entered=None;selection_done=False;finished=False;button_log=[];last_page=None;graphic_checks=[];verified=set();stable=None;stable_since=0
    # Expected compiler pagination is read from runtime pages; identify combats by
    # their unique WIN/LOSE pair and compare real player/CPU IDs at battle entry.
    for frame in range(50000):
        buttons=set()
        key=(ram[0x20],ram[0x22],ram[0x1e54],ram[0x1e55])
        if key!=stable:stable=key;stable_since=frame
        if manifest and key[:2]==(12,12) and frame-stable_since>=5:
            page=manifest['page_scenes'][key[2]];variants=page.get('graphics',[])
            gid=variants[key[3]] if key[3]<len(variants) else None
            if gid is not None and (key[2],key[3]) not in verified:
                image=s.image();canonical=b''.join(rgb555(p).to_bytes(2,'little') for p in pixels_of(image))
                digest=hashlib.sha256(canonical).hexdigest()
                assert digest==manifest['graphic_metrics'][gid]['expected_rgb555_sha256'],('Graphic pixels differ',frame,key[2],key[3],gid)
                verified.add((key[2],key[3]));graphic_checks.append(dict(page=key[2],choice=key[3],graphic=gid,rgb555_sha256=digest))
        if 420<=frame<423:buttons={3}
        if 900<=frame<903 or 1200<=frame<1203:buttons={8}
        if frame>1250 and ram[0x20]==12 and frame-last>80:
            if active is not None:
                target=ram[0x1e57 if lose else 0x1e56]
                assert ram[0x1e54]==target,(frame,'wrong result page')
                records[-1]['returned_page']=target;active=None;entered=None;selection_done=False
                # Leave the first result page on screen long enough for pixel QA.
                last=frame;s.buttons=set();s.run();continue
            page=ram[0x1e54]
            # Combat pages are recognizable in the emitted map as CHOISIS TON...
            vram=s.memory(3,65536);text=''.join(chr((int.from_bytes(vram[o:o+2],'little')&1023)+32) for o in range(0x4000,0x4800,2))
            node=manifest['page_scenes'][page] if manifest else None
            is_combat=node['kind']=='combat' if node else 'CHOISIS TON COMBATTANT' in text
            if is_combat and second and not selection_done:
                buttons={5};selection_done=True
            else:buttons={8}
            last=frame;button_log.append([frame,sorted(buttons),page])
            if (node and node['kind']=='ending') or (not node and 'A VOUS DE CONTINUER' in text):
                finished=True;break
        if ram[0x20]==1 and ram[0x22]==1:
            if active is None:
                index=len(records);assert index<len(combats),'Unexpected extra fight'
                c=combats[index]['combat'];player=c['opponent'] if second else c['player'];cpu=c['player'] if second else c['opponent']
                assert ram[0x500]==FIGHTER_IDS[player],(frame,'player ID',ram[0x500],player)
                assert ram[0x700]==FIGHTER_IDS[cpu],(frame,'CPU ID',ram[0x700],cpu)
                active=index;entered=frame;records.append(dict(scene=combats[index]['id'],player=player,cpu=cpu,arena=ram[0xbab],entry_frame=frame,result='lose' if lose else 'win'))
            if frame-entered>120 and not natural:
                hp=0x562 if lose else 0x762;ram[hp]=ram[hp+1]=0
        s.buttons=buttons;s.run()
    assert finished and len(records)==3 and all('returned_page' in r for r in records),records
    # B must leave Story and allow a fresh campaign start.
    s.buttons={0};s.run(3);s.buttons=set();s.run(150)
    assert ram[0x20]==6,('B return',ram[0x20])
    s.close()
    return dict(graphic_checks=graphic_checks,second_player=second,lose=lose,natural_match=natural,frames=frame,combats=records,rom_sha256=hashlib.sha256(raw).hexdigest(),buttons=button_log)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('core');p.add_argument('rom');p.add_argument('project');p.add_argument('--second',action='store_true');p.add_argument('--lose',action='store_true');p.add_argument('--natural',action='store_true');p.add_argument('--manifest');p.add_argument('--out',required=True);a=p.parse_args()
    result=run(a.core,a.rom,a.project,a.second,a.lose,a.natural,a.manifest);Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print('Campaign passed:',len(result['combats']),'battles,',result['frames'],'frames')
