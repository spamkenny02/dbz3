#!/usr/bin/env python3
"""Compile an editor graph into a text-scene campaign with real native battles.

Original intro/menu preserved. No SRAM. SB2 image composition is not compiled.
"""
import argparse, hashlib, json, tempfile, textwrap, unicodedata, sys
from pathlib import Path
import build_story_prototype as base
# Repository: editor/model.py. Standalone ZIP: model.py beside app.py.
ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / 'editor' if (ROOT / 'editor' / 'model.py').is_file() else ROOT
sys.path.insert(0, str(MODEL_DIR))
from model import load_project, validate

FIGHTER_IDS={'Goku':0,'Vegeta':1,'Gohan':2,'Goten':3,'Trunks':4,
             'Majin Buu':5,'Dabra':6,'C18':7,'Petit Buu':8,'Trunks (futur)':9}
# Native terrain 6 is a rocky plain; no forest is claimed.
ARENA_IDS={'tournoi':0,'salle_gravite':5,'plaine_rocheuse':6}
CODE_OFFSET=0x208000
CURRENT=0x7e1e54
CHOICE=0x7e1e55
WIN=0x7e1e56
LOSE=0x7e1e57
ACTIVE=0x7e1e58
RESUME=0x7e1e59
MAP_BANK=0x7e1e60
REQUEST=0x7e1e61
COUNT=0x7e1e62

class Asm(base.Asm65816):
    def finish(self):
        result=bytearray(super().finish())
        for kind,pos,_ in self.fixups:
            if kind!='rel8':result[pos+2]=0xc1
        return bytes(result)
    def lda(self,addr):self.emit(0xaf,addr&255,addr>>8&255,addr>>16)
    def sta(self,addr):self.emit(0x8f,addr&255,addr>>8&255,addr>>16)
    def put(self,addr,value):self.emit(0xa9,value);self.sta(addr)

def ascii_text(s):
    s=s.replace('…','...').replace('’',"'").replace('œ','oe').replace('—','-')
    return unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().upper()

def compile_campaign(data,rom):
    errors=validate(data)
    if errors:raise ValueError('\n'.join(errors))
    scenes=data['scenes'];ids={s['id']:i for i,s in enumerate(scenes)}
    if len(scenes)>200:raise ValueError('Maximum 200 nodes for this compiler')
    maps=[];pages=[]
    def add_map(lines,cursor=None):
        index=len(maps);bank=0xc2+index//16;address=0x8000+(index%16)*0x800
        if bank>=0x100:raise ValueError('Campaign exceeds expanded ROM')
        maps.append(base.make_map(lines,cursor));return bank,address
    # Dialogue is paginated instead of silently truncating editor text.
    for i,s in enumerate(scenes):
        lines=[]
        for paragraph in ascii_text(s.get('dialogue','')).splitlines():
            lines.extend(textwrap.wrap(paragraph,28) or [''])
        chunks=[lines[j:j+9] for j in range(0,len(lines),9)] or [[]]
        for n,chunk in enumerate(chunks):
            rows=[(2,ascii_text(s['name'])[:30],1,'center')]
            rows += [(5+k*2,line,0,'left:2') for k,line in enumerate(chunk)]
            rows += [(25,'A : CONTINUER   B : MENU',1,'center')]
            options=[]
            if s['kind']=='combat':
                c=s['combat'];options=[c['player'],c['opponent']] if c.get('selectable') else [c['player']]
                rows=[(2,ascii_text(s['name'])[:30],1,'center'),(6,'CHOISIS TON COMBATTANT',0,'center')]
                rows += [(12+k*4,ascii_text(name),1,'center') for k,name in enumerate(options)]
                rows += [(22,'A : COMBATTRE   B : MENU',0,'center')]
            elif s.get('choices') and n==len(chunks)-1:
                options=[c['label'] for c in s['choices']]
                rows=[(2,ascii_text(s['name'])[:30],1,'center')]+[(5+k,line,0,'left:2') for k,line in enumerate(chunk[:9])]
                rows += [(16+k*3,ascii_text(t)[:26],1,'center') for k,t in enumerate(options)]
            variants=[]
            for selected in range(max(1,len(options))):
                cursor=(12+selected*4 if s['kind']=='combat' else 16+selected*3) if options else None
                variants.append(add_map(rows,cursor))
            pages.append(dict(scene=i,part=n,parts=len(chunks),variants=variants,options=options))
    first={i:next(j for j,p in enumerate(pages) if p['scene']==i) for i in range(len(scenes))}
    if len(pages)>250:raise ValueError('Dialogue pagination exceeds 250 pages')
    a=Asm(0x8000)
    a.label('Init')
    a.emit(0xe2,0x20,0xc2,0x10);a.lda(RESUME);a.emit(0xc9,1);a.branch(0xf0,'Resume')
    a.put(CURRENT,first[ids[data['start']]])
    a.label('Resume');a.put(RESUME,0);a.put(ACTIVE,0);a.put(CHOICE,0);a.jsl('Render')
    a.emit(0x5c,0x1d,0x81,0x80)
    a.label('Frame')
    a.emit(0x08,0x8b,0xe2,0x20,0xc2,0x10,0xa9,0,0x48,0xab)
    a.lda(0x7e006e);a.emit(0x29,0x80);a.branch(0xf0,'CheckA')
    a.put(ACTIVE,0);a.put(RESUME,0);a.put(0x7e1878,2);a.put(0x7e1879,0);a.emit(0xa9,6,0x5c,0x7a,0x80,0x80)
    a.label('CheckA');a.lda(0x7e006d);a.emit(0x29,0x80);a.branch(0xf0,'Move')
    a.emit(0xab,0x28);a.jml('Dispatch')
    a.label('Move');a.lda(0x7e006e);a.emit(0x29,0x0c);a.branch(0xf0,'Done')
    a.lda(0x7e006e);a.emit(0x29,8);a.branch(0xf0,'MoveDown')
    a.lda(CHOICE);a.branch(0xd0,'MoveUpNormal');a.lda(COUNT)
    a.label('MoveUpNormal');a.emit(0x3a);a.branch(0x80,'StoreChoice')
    a.label('MoveDown');a.lda(CHOICE);a.emit(0x1a);a.sta(CHOICE);a.lda(COUNT)
    # Compare against COUNT without using direct-page assumptions.
    a.emit(0xcf,CHOICE&255,CHOICE>>8&255,CHOICE>>16);a.branch(0xd0,'RedrawChoice');a.emit(0xa9,0)
    a.label('StoreChoice');a.sta(CHOICE)
    a.label('RedrawChoice');a.jsl('Render')
    a.label('Done');a.emit(0xab,0x28,0x6b)
    a.label('Dispatch')
    a.emit(0xe2,0x20,0xc2,0x10)
    for n in range(len(pages)):
        a.lda(CURRENT);a.emit(0xc9,n);a.branch(0xd0,f'dispatch_skip{n}');a.jml(f'page{n}');a.label(f'dispatch_skip{n}')
    a.emit(0x6b)
    for n,p in enumerate(pages):
        s=scenes[p['scene']];a.label(f'page{n}')
        if s['kind']=='combat':
            c=s['combat'];a.put(WIN,first[ids[c['win']]]);a.put(LOSE,first[ids[c['lose']]])
            a.put(ACTIVE,1);a.put(RESUME,0)
            for addr,value in {0x501:0,0x701:0,0x517:0,0x717:0,0x169d:1,0x169e:0,0x169b:0,0x169c:0,0x16a6:0,0x188c:1,0x19ae:0,0x19af:0,0x166e:0,0x166f:0,0x18a1:0,0x1b0a:7,0xbab:ARENA_IDS[c.get('arena','plaine_rocheuse')]}.items():a.put(0x7e0000+addr,value)
            p1=FIGHTER_IDS[c['player']];p2=FIGHTER_IDS[c['opponent']]
            if c.get('selectable'):
                a.lda(CHOICE);a.emit(0xc9,1);a.branch(0xd0,f'normal{n}')
                a.put(0x7e0500,p2);a.put(0x7e0700,p1);a.jml(f'launch{n}');a.label(f'normal{n}')
            a.put(0x7e0500,p1);a.put(0x7e0700,p2)
            a.label(f'launch{n}');a.emit(0xa9,0x80,0x48,0xab,0x5c,0x87,0xcf,0xbf)
        else:
            if p['part']<p['parts']-1:target=n+1
            elif s.get('choices'):
                for ci,ch in enumerate(s['choices']):
                    a.lda(CHOICE);a.emit(0xc9,ci);a.branch(0xd0,f'choice_skip{n}_{ci}')
                    a.put(CURRENT,first[ids[ch['target']]]);a.jml('Advance');a.label(f'choice_skip{n}_{ci}')
                target=first[ids[s['choices'][0]['target']]]
            else:target=first[ids[s['next']]] if s.get('next') else first[ids[data['start']]]
            a.put(CURRENT,target);a.jml('Advance')
    a.label('Advance');a.put(CHOICE,0);a.jsl('Render');a.emit(0x6b)
    a.label('Render')
    a.emit(0x08,0xc2,0x30,0x48,0xda,0x5a,0xe2,0x20)
    for n,p in enumerate(pages):
        a.lda(CURRENT);a.emit(0xc9,n);a.branch(0xd0,f'render_skip{n}');a.jml(f'map{n}');a.label(f'render_skip{n}')
    a.jml('Rendered')
    for n,p in enumerate(pages):
        a.label(f'map{n}');a.put(COUNT,len(p['variants']))
        # Clamp a shared 0..2 cursor to the number of choices on this page.
        a.lda(CHOICE);a.emit(0xc9,len(p['variants']));a.branch(0x90,f'clamped{n}');a.put(CHOICE,0);a.label(f'clamped{n}')
        for ci,(bank,address) in enumerate(p['variants']):
            a.lda(CHOICE);a.emit(0xc9,ci);a.branch(0xd0,f'variant_skip{n}_{ci}')
            a.put(MAP_BANK,bank);a.emit(0xa2,address&255,address>>8);a.jsl('Draw');a.jml('Rendered');a.label(f'variant_skip{n}_{ci}')
        a.jml('Rendered')
    a.label('Rendered');a.emit(0xc2,0x30,0x7a,0xfa,0x68,0x28,0x6b)
    # Intercept only a completed story battle returning through the native flow.
    a.label('Transition');a.emit(0xe2,0x20);a.sta(REQUEST)
    a.lda(ACTIVE);a.emit(0xc9,1);a.branch(0xd0,'NativeTransition')
    a.lda(REQUEST);a.emit(0xc9,6);a.branch(0xd0,'NativeTransition')
    a.lda(0x7e0020);a.emit(0x29,0x7f,0xc9,1);a.branch(0xd0,'NativeTransition')
    # Native health is a 16-bit word; slot zero is always the human player.
    a.emit(0xc2,0x20);a.lda(0x7e0562);a.emit(0xc9,0,0,0xe2,0x20);a.branch(0xf0,'PlayerLost')
    a.lda(WIN);a.branch(0x80,'StoreResult')
    a.label('PlayerLost');a.lda(LOSE)
    a.label('StoreResult');a.sta(CURRENT);a.put(RESUME,1);a.put(ACTIVE,0);a.put(REQUEST,12)
    a.label('NativeTransition');a.lda(REQUEST)
    a.emit(0xe2,0x20,0xa2,0xfe,0x1f,0x9a,0x5c,0x80,0x80,0x80)
    a.label('Draw')
    original,labels=base.assemble_code();draw=original[labels['DrawScreen']-base.CODE_CPU_START:labels['NativeMenuAddStory']-base.CODE_CPU_START]
    old=bytes.fromhex('8e 02 43 a9 c0 8d 04 43');new=bytes.fromhex('8e 02 43 af 60 1e 7e 8d 04 43')
    if draw.count(old)!=1:raise ValueError('Renderer DMA signature changed')
    a.emit(*draw.replace(old,new))
    code=a.finish()
    if len(code)>0x8000:raise ValueError('Campaign code exceeds bank C1')
    rom[CODE_OFFSET:CODE_OFFSET+len(code)]=code
    for n,tilemap in enumerate(maps):
        offset=0x210000+n*0x800;rom[offset:offset+0x800]=tilemap
    rom[base.INIT_TABLE_OFFSET+12*3:base.INIT_TABLE_OFFSET+13*3]=base.pointer3(0xc10000+a.labels['Init'])
    rom[base.FRAME_TABLE_OFFSET+12*3:base.FRAME_TABLE_OFFSET+13*3]=base.pointer3(0xc10000+a.labels['Frame'])
    if rom[0x7a:0x80]!=bytes.fromhex('e2 20 a2 fe 1f 9a'):raise ValueError('Native transition signature changed')
    rom[0x7a:0x80]=bytes([0x5c])+base.pointer3(0xc10000+a.labels['Transition'])+bytes.fromhex('ea ea')
    base.update_checksum(rom)
    return dict(scenes=len(scenes),pages=len(pages),maps=len(maps),code_bytes=len(code),labels={k:f'C1:{v:04X}' for k,v in a.labels.items()},graphics_compiled=False,arena_ids=ARENA_IDS,fighter_ids=FIGHTER_IDS)

def build(rom_path,project_path,out_rom,out_ips,report_path):
    paths=[Path(p).resolve() for p in (rom_path,project_path,out_rom,out_ips,report_path)]
    if len(set(paths))!=len(paths):raise ValueError('Input and output paths must all differ')
    data=load_project(project_path)
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d);base.build(Path(rom_path),tmp/'base.sfc',tmp/'base.ips')
        rom=bytearray((tmp/'base.sfc').read_bytes())
    report=compile_campaign(data,rom);original=Path(rom_path).read_bytes();ips=base.make_ips(original,bytes(rom))
    for path,payload in [(out_rom,rom),(out_ips,ips)]:Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(payload)
    report.update(rom_sha256=hashlib.sha256(rom).hexdigest(),ips_sha256=hashlib.sha256(ips).hexdigest(),base_sha256=base.BASE_SHA256,emulator_tested=False)
    Path(report_path).write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('project');p.add_argument('--out-rom',default='build/campaign.sfc');p.add_argument('--out-ips',default='build/campaign.ips');p.add_argument('--report',default='build/campaign.json');args=p.parse_args()
    print(json.dumps(build(args.rom,args.project,args.out_rom,args.out_ips,args.report),indent=2))
