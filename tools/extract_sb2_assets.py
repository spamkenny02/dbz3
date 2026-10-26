#!/usr/bin/env python3
"""Extract scene backgrounds and transparent OBJ art from the supplied SB2 ROM.

Requires Pillow and the diagnostic Snes9x core (emulator-tools/README.md).
The original ROM is never written. Probes are made only in an in-memory copy.
"""
import argparse, hashlib, json
from pathlib import Path
from libretro_session import Session
from snes_graphics import objects, split_objects

def probe_rom(original, scene):
    if len(original)!=0x400000:raise ValueError('This extractor targets the supplied 4 MiB SB2 Tools ROM')
    if original[0x1F8474:0x1F8478]!=bytes.fromhex('E2 20 A5 20'):raise ValueError('Scene initialization hook does not match')
    if set(original[0x3FF000:0x3FF020])!={255}:raise ValueError('Diagnostic scratch bank is not empty')
    data=bytearray(original);data[0x7FA0]=5
    data[0x1F8474:0x1F8478]=bytes.fromhex('22 00 F0 FF')
    code=bytes.fromhex('E2 20 A9')+bytes([scene])+bytes.fromhex('8D 12 1B A9 01 8D 21 1B A5 20 6B')
    data[0x3FF000:0x3FF000+len(code)]=code
    return bytes(data)

def extract(rom,core,destination,ids):
    original=Path(rom).read_bytes();out=Path(destination);out.mkdir(parents=True,exist_ok=True)
    (out/'images').mkdir(exist_ok=True)
    catalog={'version':1,'source_sha256':hashlib.sha256(original).hexdigest(),
             'source_title':original[0x7fc0:0x7fd5].decode('ascii','replace').strip(),
             'method':'runtime scene initialization; decoded 4bpp OBJ + CGRAM; BG render with OBJ disabled',
             'limits':['No combat animations or all possible dynamic poses claimed',
                       'OBJ art is unblended; special window/color-math effects are not baked in',
                       'Nearby alpha components are grouped; overlapping characters/props may remain combined'],
             'attempted_scene_ids':len(ids), 'assets':[], 'scenes':[], 'errors':[]}
    seen={};session=Session(core)
    def save(im,kind,label,scene,**extra):
        digest=hashlib.sha256(im.mode.encode()+str(im.size).encode()+im.tobytes()).hexdigest()
        key=(kind,digest)
        if key not in seen:
            aid=f'{kind}_{len(seen):04d}';path=f'images/{aid}.png';im.save(out/path)
            record=dict(id=aid,kind=kind,name=label,path=path,width=im.width,height=im.height,
                        sha256=digest,source_scenes=[scene],**extra)
            seen[key]=record;catalog['assets'].append(record)
        else:
            record=seen[key];record['source_scenes'].append(scene)
        return record['id']
    try:
        for num,scene in enumerate(ids):
            try:
                session.layers(set());session.load(probe_rom(original,scene));session.run(650)
                ram=session.memory(2,131072)
                if ram[0x20]!=5 or ram[0x1b12]!=scene:
                    raise ValueError(f'Runtime scene not verified: global={ram[0x20]:02X}, scene={ram[0x1b12]:02X}')
                vram=session.memory(3,65536)
                cgram=session.memory(42,512);oam=session.memory(43,544);regs=session.memory(44,32768)
                sprite,indices=objects(vram,cgram,oam,regs[0x2101])
                session.layers({5});session.run(2);background=session.image().convert('RGBA')
                bid=save(background,'background',f'Décor scène {scene:02X}',scene)
                actor_ids=[]
                for part_index,(crop,origin) in enumerate(split_objects(sprite)):
                    aid=save(crop,'sprite',f'Élément {part_index+1} · scène {scene:02X}',scene,
                             origin=origin,oam_indices=indices)
                    actor_ids.append(aid)
                pointer=int.from_bytes(original[0x1FC35E+scene*2:0x1FC360+scene*2],'little')
                catalog['scenes'].append(dict(id=scene,descriptor=f'BF:{pointer:04X}',background=bid,sprites=actor_ids,
                                             runtime_global=ram[0x20],runtime_scene=ram[0x1b12]))
            except Exception as error:catalog['errors'].append(dict(scene=scene,error=str(error)))
            (out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print(f'{num+1}/{len(ids)} scène {scene:02X}: {len(catalog["assets"])} assets uniques',flush=True)
    finally:session.close()
    return catalog

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom');parser.add_argument('core');parser.add_argument('destination')
    parser.add_argument('--ids',default='00-FF',help='Hex ids/ranges, e.g. 02,10-20')
    args=parser.parse_args();ids=[]
    for chunk in args.ids.split(','):
        ends=[int(x,16) for x in chunk.split('-')];ids.extend(range(ends[0],ends[-1]+1))
    if any(not 0<=i<=255 for i in ids):parser.error('Scene IDs must be 00..FF')
    extract(args.rom,args.core,args.destination,list(dict.fromkeys(ids)))
