#!/usr/bin/env python3
"""Compile editor compositions and scene graphs into SNES story campaigns.

Original intro/menu preserved. No SRAM. Static compositions use Mode 3 BG1.
"""
import argparse, hashlib, json, tempfile, textwrap, unicodedata, sys
from pathlib import Path
import build_story_prototype as base
# Repository: editor/model.py. Standalone ZIP: model.py beside app.py.
ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / 'editor' if (ROOT / 'editor' / 'model.py').is_file() else ROOT
sys.path.insert(0, str(MODEL_DIR))
from model import load_project, validate, Assets, compose
from story_graphics import encode, page_image, Payloads, reveal_image
from sb2_style import NativeFont
import base64

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
TEXT_POS=0x7e1e68
TEXT_TICK=0x7e1e69
TEXT_LENGTH=0x7e1e6a
AUTO_TIMER=0x7e1e6c
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

def compile_campaign(data,rom,assets=None,style=None):
    errors=validate(data)
    if data.get('music',{}).get('source')=='sb2' and style is None:errors.append('Ressources musicales SB2 manquantes : préparez la première scène SB2.')
    if errors:raise ValueError('\n'.join(errors))
    scenes=data['scenes'];ids={s['id']:i for i,s in enumerate(scenes)}
    if len(scenes)>200:raise ValueError('Maximum 200 nodes for this compiler')
    maps=[];pages=[];pool=Payloads();graphics=[];graphic_cache={}
    needs_assets=any(s.get('background') or s.get('actors') for s in scenes)
    if needs_assets and assets is None:raise ValueError('Le projet contient des graphismes : chargez son catalogue assets/catalog.json avant de construire la ROM.')
    if assets is not None:
        errors=validate(data,assets.items)
        if errors:raise ValueError('\n'.join(errors))
    def add_map(lines,cursor=None):
        tilemap=base.make_map(lines,cursor);pointer=pool.put(tilemap)
        maps.append(tilemap);return pointer>>16,pointer&65535
    # Dialogue is paginated instead of silently truncating editor text.
    for i,s in enumerate(scenes):
        native=s.get('presentation')=='sb2'
        if native and style is None:raise ValueError('Préparez les ressources de la ROM SB2 originale pour ce style.')
        font=NativeFont(base64.b64decode(style['font'])) if native else None
        graphical=bool(s.get('background') or s.get('actors')) or native
        composition=compose(s,assets,dialogue=False) if graphical else None
        lines=[]
        for paragraph in (s.get('dialogue','') if native else ascii_text(s.get('dialogue',''))).splitlines():
            lines.extend(textwrap.wrap(paragraph.replace('’',"'"),26 if native else 28) or [''])
        per_page=3 if native else 4 if graphical else 9
        chunks=[lines[j:j+per_page] for j in range(0,len(lines),per_page)] or [[]]
        if graphical and s.get('choices') and s['kind']!='combat' and len(chunks[-1])>2:
            chunks.append([])
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
                if graphical:
                    cells=[]
                    if native:
                        screen=composition.convert('RGB').copy()
                        if options:
                            for k,option in enumerate(options):font.draw(screen,24,152+k*16,('> ' if k==selected else '  ')+option)
                        else:
                            for k,line in enumerate(chunk):
                                font.draw(screen,24,152+k*16,line)
                                cells.extend((24+ci*8,152+k*16) for ci in range(len(line)))
                    else:screen=page_image(composition,ascii_text(s['name']),chunk,[ascii_text(o) for o in options],selected,s['kind']=='combat')
                    key=screen.tobytes()
                    if key not in graphic_cache:
                        encoded=reveal_image(composition,screen,cells) if cells else encode(screen);gid=len(graphics);graphic_cache[key]=gid
                        gfx=pool.image(encoded);gfx['reveals']=encoded.get('reveals',[])
                        if gfx['reveals']:gfx['final_map']=pool.put(encoded['final_map'])
                        graphics.append(gfx)
                    variants.append(('graphic',graphic_cache[key]))
                else:variants.append(add_map(rows,cursor))
            pages.append(dict(scene=i,part=n,parts=len(chunks),variants=variants,options=options))
    first={i:next(j for j,p in enumerate(pages) if p['scene']==i) for i in range(len(scenes))}
    if len(pages)>250:raise ValueError('Dialogue pagination exceeds 250 pages')
    a=Asm(0x8000)
    a.label('Init')
    a.emit(0xe2,0x20,0xc2,0x10);a.lda(RESUME);a.emit(0xc9,1);a.branch(0xf0,'Resume')
    a.put(CURRENT,first[ids[data['start']]])
    a.label('Resume');a.put(RESUME,0);a.put(ACTIVE,0);a.put(CHOICE,0)
    a.jsl('Render')
    if style and data.get('music',{}).get('source')=='sb2':a.jsl('StartSB2')
    a.emit(0x5c,0x1d,0x81,0x80)
    a.label('Frame')
    a.emit(0x08,0x8b,0xe2,0x20,0xc2,0x10,0xa9,0,0x48,0xab)
    for pn,page in enumerate(pages):
        delay=scenes[page['scene']].get('auto_frames',0)
        if not delay:continue
        if not 1<=delay<=255:raise ValueError('auto_frames must be 1..255')
        a.lda(CURRENT);a.emit(0xc9,pn);a.branch(0xd0,f'AutoSkip{pn}')
        a.lda(AUTO_TIMER);a.emit(0x1a);a.sta(AUTO_TIMER);a.emit(0xc9,delay);a.branch(0x90,f'AutoSkip{pn}')
        a.emit(0xab,0x28);a.jml('Dispatch');a.label(f'AutoSkip{pn}')
    a.jsl('TickText')
    a.lda(0x7e006e);a.emit(0x29,0x80);a.branch(0xf0,'CheckA')
    if style and data.get('music',{}).get('source')=='sb2':a.jsl('RestoreSB3')
    a.put(ACTIVE,0);a.put(RESUME,0);a.put(0x7e1878,2);a.put(0x7e1879,0);a.emit(0xa9,6,0x5c,0x7a,0x80,0x80)
    a.label('CheckA');a.lda(0x7e006d);a.emit(0x29,0x80);a.branch(0xf0,'Move')
    a.lda(TEXT_POS);a.emit(0xcf,TEXT_LENGTH&255,TEXT_LENGTH>>8&255,TEXT_LENGTH>>16)
    a.branch(0xf0,'TextComplete')
    a.jsl('FinishText');a.emit(0xab,0x28,0x6b)
    a.label('TextComplete');a.emit(0xab,0x28);a.jml('Dispatch')
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
            if style and data.get('music',{}).get('source')=='sb2':a.jsl('RestoreSB3')
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
        a.label(f'map{n}');a.put(COUNT,len(p['variants']));a.put(TEXT_POS,0);a.put(TEXT_TICK,0);a.put(TEXT_LENGTH,0);a.put(AUTO_TIMER,0)
        # Clamp a shared 0..2 cursor to the number of choices on this page.
        a.lda(CHOICE);a.emit(0xc9,len(p['variants']));a.branch(0x90,f'clamped{n}');a.put(CHOICE,0);a.label(f'clamped{n}')
        for ci,variant in enumerate(p['variants']):
            a.lda(CHOICE);a.emit(0xc9,ci);a.branch(0xd0,f'variant_skip{n}_{ci}')
            if variant[0]=='graphic':
                a.jsl(f'Graphic{variant[1]}');a.put(TEXT_LENGTH,len(graphics[variant[1]].get('reveals',[])))
            else:
                bank,address=variant;a.put(MAP_BANK,bank);a.emit(0xa2,address&255,address>>8);a.jsl('Draw')
            a.jml('Rendered');a.label(f'variant_skip{n}_{ci}')
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
    a.label('FinishText')
    a.emit(0x08,0xe2,0x20)
    a.label('FinishAgain');a.lda(TEXT_POS);a.emit(0xcf,TEXT_LENGTH&255,TEXT_LENGTH>>8&255,TEXT_LENGTH>>16);a.branch(0xf0,'FinishDone')
    a.jsl('RevealOne');a.branch(0x80,'FinishAgain')
    a.label('FinishDone');a.emit(0x28,0x6b)
    a.label('TickText');a.emit(0x08,0xe2,0x20);a.lda(TEXT_POS);a.emit(0xcf,TEXT_LENGTH&255,TEXT_LENGTH>>8&255,TEXT_LENGTH>>16);a.branch(0xf0,'TickDone')
    a.lda(TEXT_TICK);a.emit(0x1a);a.sta(TEXT_TICK);a.emit(0xc9,3);a.branch(0x90,'TickDone');a.put(TEXT_TICK,0);a.jsl('RevealOne')
    a.label('TickDone');a.emit(0x28,0x6b)
    a.label('RevealOne');a.emit(0x08,0xc2,0x30,0x48,0xda,0x5a,0xe2,0x20)
    for pn,page in enumerate(pages):
        variant=page['variants'][0]
        if variant[0]!='graphic' or not graphics[variant[1]].get('reveals'):continue
        a.lda(CURRENT);a.emit(0xc9,pn);a.branch(0xd0,f'RevealSkip{pn}');a.jml(f'RevealPage{pn}');a.label(f'RevealSkip{pn}')
    a.jml('Revealed')
    for pn,page in enumerate(pages):
        variant=page['variants'][0]
        if variant[0]!='graphic' or not graphics[variant[1]].get('reveals'):continue
        a.label(f'RevealPage{pn}')
        table=b''.join((0x7800+offset//2).to_bytes(2,'little')+top.to_bytes(2,'little')+bottom.to_bytes(2,'little') for offset,top,bottom in graphics[variant[1]]['reveals'])
        pointer=pool.put(table)
        a.emit(0xc2,0x30);a.lda(TEXT_POS);a.emit(0x29,0xff,0,0x0a,0x85,0,0x0a,0x18,0x65,0,0xaa,0xe2,0x20,0xa9,0x80,0x8d,0x15,0x21,0xc2,0x20)
        def table_word(add):a.emit(0xbf,(pointer+add)&255,(pointer+add)>>8&255,(pointer+add)>>16)
        table_word(0);a.emit(0x8d,0x16,0x21)
        table_word(2);a.emit(0x8d,0x18,0x21)
        table_word(0);a.emit(0x18,0x69,0x20,0,0x8d,0x16,0x21)
        table_word(4);a.emit(0x8d,0x18,0x21,0xe2,0x20)
        a.lda(TEXT_POS);a.emit(0x1a);a.sta(TEXT_POS)
        a.jml('Revealed')
    a.label('Revealed');a.emit(0xc2,0x30,0x7a,0xfa,0x68,0x28,0x6b)
    a.label('Draw')
    original,labels=base.assemble_code();draw=original[labels['DrawScreen']-base.CODE_CPU_START:labels['NativeMenuAddStory']-base.CODE_CPU_START]
    old=bytes.fromhex('8e 02 43 a9 c0 8d 04 43');new=bytes.fromhex('8e 02 43 af 60 1e 7e 8d 04 43')
    if draw.count(old)!=1:raise ValueError('Renderer DMA signature changed')
    a.emit(*draw.replace(old,new))
    # Bitmap renderer: Mode 3 BG1, 256 colors, map at VRAM byte F000.
    # Each routine uses only bank-contained DMA payloads, under forced blank.
    def write(addr,value):a.emit(0xa9,value,0x8d,addr&255,addr>>8)
    def dma(pointer,length,register,mode,dest=None):
        if dest is not None:write(0x2116,dest&255);write(0x2117,dest>>8)
        for addr,value in {0x4300:mode,0x4301:register,0x4302:pointer&255,0x4303:pointer>>8&255,0x4304:pointer>>16,0x4305:length&255,0x4306:length>>8,0x420b:1}.items():write(addr,value)
    for gi,gfx in enumerate(graphics):
        a.label(f'Graphic{gi}')
        a.emit(0x08,0x8b,0xc2,0x30,0x48,0xda,0x5a,0xe2,0x20,0xa9,0,0x48,0xab)
        a.lda(0x7e0b43);a.emit(0x48);a.put(0x7e0b43,0);write(0x4200,0);write(0x2100,0x80)
        shadows={0x0b2a:3,0x0b2b:0,0x0b2c:0x78,0x0b2d:0,0x0b2e:0,0x0b30:0,0x0b31:0,0x0b39:1,0x0b3a:0,0x0b3d:0,0x0b3e:0,0x0b45:0,0x0b27:15,**{n:0 for n in range(0x0b68,0x0b78)}}
        for addr,value in shadows.items():a.put(0x7e0000+addr,value)
        for addr in range(0x83,0x93):a.put(0x7e0000+addr,0)
        # SNES renders scanline 1 first: VOFS -1 retains bitmap row zero.
        for addr in (0x7e0085,0x7e0086,0x7e0b6a,0x7e0b6b):a.put(addr,255)
        for addr,value in {0x2105:3,0x2106:0,0x2107:0x78,0x210b:0,0x212c:1,0x212d:0,0x2130:0,0x2131:0,0x2115:0x80}.items():write(addr,value)
        write(0x210d,0);write(0x210d,0);write(0x210e,255);write(0x210e,255)
        for pointer,length,dest in gfx['segments']:dma(pointer,length,0x18,1,dest)
        dma(gfx['map'],0x800,0x18,1,0x7800)
        write(0x2121,0);dma(gfx['palette'],512,0x22,0)
        write(0x2100,15)
        a.emit(0x68,0x09,0x80);a.sta(0x7e0b43);a.emit(0x8d,0,0x42,0xc2,0x30,0x7a,0xfa,0x68,0xab,0x28,0x6b)
    audio_sites=[]
    if style and data.get('music',{}).get('source')=='sb2':
        from story_audio import append_audio
        audio_sites=append_audio(a,pool,style,data['music'].get('track',4),rom)
    code=a.finish()
    if len(code)>0x8000:raise ValueError('Campaign code exceeds bank C1')
    rom[CODE_OFFSET:CODE_OFFSET+len(code)]=code
    # Legacy text maps also go through the same allocator to avoid overlap.
    # Their addresses were reserved while constructing page variants.
    pool.install(rom)
    rom[base.INIT_TABLE_OFFSET+12*3:base.INIT_TABLE_OFFSET+13*3]=base.pointer3(0xc10000+a.labels['Init'])
    rom[base.FRAME_TABLE_OFFSET+12*3:base.FRAME_TABLE_OFFSET+13*3]=base.pointer3(0xc10000+a.labels['Frame'])
    if rom[0x7a:0x80]!=bytes.fromhex('e2 20 a2 fe 1f 9a'):raise ValueError('Native transition signature changed')
    rom[0x7a:0x80]=bytes([0x5c])+base.pointer3(0xc10000+a.labels['Transition'])+bytes.fromhex('ea ea')
    for offset,label in audio_sites:rom[offset:offset+4]=bytes([0x22])+base.pointer3(0xc10000+a.labels[label])
    base.update_checksum(rom)
    return dict(sb2_font_sha256=style.get('font_sha256') if style else None,sb2_driver_prefix_sha256=hashlib.sha256(base64.b64decode(next(b['data'] for b in style['audio']['0']['blocks'] if b['destination']==0x800))[:64]).hexdigest() if style else None,music=data.get('music'),page_scenes=[dict(scene=scenes[p['scene']]['id'],kind=scenes[p['scene']]['kind'],part=p['part'],options=len(p['options']),graphics=[v[1] if v[0]=='graphic' else None for v in p['variants']]) for p in pages],scenes=len(scenes),pages=len(pages),maps=len(maps),code_bytes=len(code),labels={k:f'C1:{v:04X}' for k,v in a.labels.items()},graphics_compiled=bool(graphics),graphic_variants=len(graphics),graphic_metrics=[g['metrics'] for g in graphics],payload_end=hex(pool.cursor),arena_ids=ARENA_IDS,fighter_ids=FIGHTER_IDS)

def build(rom_path,project_path,out_rom,out_ips,report_path):
    paths=[Path(p).resolve() for p in (rom_path,project_path,out_rom,out_ips,report_path)]
    if len(set(paths))!=len(paths):raise ValueError('Input and output paths must all differ')
    data=load_project(project_path)
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d);base.build(Path(rom_path),tmp/'base.sfc',tmp/'base.ips')
        rom=bytearray((tmp/'base.sfc').read_bytes())
    assets=None
    if any(s.get('background') or s.get('actors') for s in data['scenes']):
        catalog=(Path(project_path).resolve().parent/data.get('catalog','assets/catalog.json')).resolve()
        if not catalog.is_file():raise ValueError(f'Catalogue graphique introuvable : {catalog}. Chargez le catalogue dans l’éditeur.')
        assets=Assets(catalog)
    style=None
    if data.get('sb2_style'):style=json.loads((Path(project_path).resolve().parent/data['sb2_style']).resolve().read_text())
    report=compile_campaign(data,rom,assets,style);original=Path(rom_path).read_bytes();ips=base.make_ips(original,bytes(rom))
    for path,payload in [(out_rom,rom),(out_ips,ips)]:Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_bytes(payload)
    report.update(rom_sha256=hashlib.sha256(rom).hexdigest(),ips_sha256=hashlib.sha256(ips).hexdigest(),base_sha256=base.BASE_SHA256,emulator_tested=False)
    Path(report_path).write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('project');p.add_argument('--out-rom',default='build/campaign.sfc');p.add_argument('--out-ips',default='build/campaign.ips');p.add_argument('--report',default='build/campaign.json');args=p.parse_args()
    print(json.dumps(build(args.rom,args.project,args.out_rom,args.out_ips,args.report),indent=2))
