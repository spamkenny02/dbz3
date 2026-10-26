#!/usr/bin/env python3
"""Exercise the full campaign with Snes9x; inject KOs to test both return paths.
This validates battle entry/result routing, not a human-played complete match.
"""
import argparse, ctypes as C, hashlib, json, sys
from pathlib import Path
from libretro_session import Session
from build_story_campaign import FIGHTER_IDS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'editor'))
from model import load_project

def run(core,rom,project,second=False,lose=False,natural=False):
    s=Session(core);raw=Path(rom).read_bytes();s.load(raw)
    ram=(C.c_ubyte*131072).from_address(s.lib.retro_get_memory_data(2))
    data=load_project(project);combats=[n for n in data['scenes'] if n['kind']=='combat'];records=[]
    last=-200;active=None;entered=None;selection_done=False;finished=False;button_log=[];last_page=None
    # Expected compiler pagination is read from runtime pages; identify combats by
    # their unique WIN/LOSE pair and compare real player/CPU IDs at battle entry.
    for frame in range(50000):
        buttons=set()
        if 420<=frame<423:buttons={3}
        if 900<=frame<903 or 1200<=frame<1203:buttons={8}
        if frame>1250 and ram[0x20]==12 and frame-last>80:
            if active is not None:
                target=ram[0x1e57 if lose else 0x1e56]
                assert ram[0x1e54]==target,(frame,'wrong result page')
                records[-1]['returned_page']=target;active=None;entered=None;selection_done=False
            page=ram[0x1e54]
            # Combat pages are recognizable in the emitted map as CHOISIS TON...
            vram=s.memory(3,65536);text=''.join(chr((int.from_bytes(vram[o:o+2],'little')&1023)+32) for o in range(0x4000,0x4800,2))
            if 'CHOISIS TON COMBATTANT' in text and second and not selection_done:
                buttons={5};selection_done=True
            else:buttons={8}
            last=frame;button_log.append([frame,sorted(buttons),page])
            if 'A VOUS DE CONTINUER' in text:
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
    return dict(second_player=second,lose=lose,natural_match=natural,frames=frame,combats=records,rom_sha256=hashlib.sha256(raw).hexdigest(),buttons=button_log)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('core');p.add_argument('rom');p.add_argument('project');p.add_argument('--second',action='store_true');p.add_argument('--lose',action='store_true');p.add_argument('--natural',action='store_true');p.add_argument('--out',required=True);a=p.parse_args()
    result=run(a.core,a.rom,a.project,a.second,a.lose,a.natural);Path(a.out).write_text(json.dumps(result,indent=2)+'\n');print('Campaign passed:',len(result['combats']),'battles,',result['frames'],'frames')
