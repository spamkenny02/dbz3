#!/usr/bin/env python3
"""Validate the SB2-style first scene, typewriter, music and native battle return.
Requires the diagnostic core's read-only APURAM export 45 for driver checking.
Outcome coverage injects a KO unless --natural is supplied.
"""
import argparse,array,ctypes as C,hashlib,json
from pathlib import Path
from libretro_session import Session
from story_graphics import pixels_of,rgb555
from story_audio import native_sb3_packages

def run(core,rom_path,manifest_path,second=False,lose=False,natural=False):
    raw=Path(rom_path).read_bytes();manifest=json.loads(Path(manifest_path).read_text());s=Session(core);s.load(raw)
    ram=(C.c_ubyte*131072).from_address(s.lib.retro_get_memory_data(2));peaks={'sb2':0,'sb3_battle':0};frame=0
    @C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t)
    def audio(data,n):
        category='sb2' if ram[0x20]==12 and ram[0x1e64]==1 else 'sb3_battle' if ram[0x20]==1 and ram[0x1e64]==0 else None
        if category and n:
            values=array.array('h',C.string_at(data,n*4));peaks[category]=max(peaks[category],max(map(abs,values)))
        return n
    s.lib.retro_set_audio_sample_batch(audio)
    verified=[];keys=set();entered=None;returned=False;selected=False;last_action=-200;stable=None;since=0;finished=False;typewriter_samples=[];skipped=False;skip_page=None
    driver_prefix=native_sb3_packages(raw)[0][0][0][1][:64]
    for frame in range(20000):
        buttons=set()
        if 420<=frame<423:buttons={3}
        if 900<=frame<903 or 1200<=frame<1203:buttons={8}
        key=(ram[0x20],ram[0x22],ram[0x1e54],ram[0x1e55])
        if key!=stable:stable=key;since=frame
        if key[:2]==(12,12):
            page=manifest['page_scenes'][key[2]];scene=page['scene']
            assert ram[0x1e66]==0,('SPC upload failed',frame,scene)
            assert ram[0x1e64]==1
            assert hashlib.sha256(s.memory(45,65536)[0x800:0x840]).hexdigest()==manifest['sb2_driver_prefix_sha256'],'SB2 SPC driver missing'
            if entered is not None and not returned:
                assert scene==('lose' if lose else 'win'),(scene,lose)
                returned=True
            if scene=='gohan':
                if not typewriter_samples or typewriter_samples[-1]['letters']!=ram[0x1e68]:typewriter_samples.append(dict(frame=frame,letters=ram[0x1e68]))
                if 12<=ram[0x1e68]<ram[0x1e6a] and not skipped:
                    buttons={8};skipped=True;skip_page=key[2];last_action=frame
            if skip_page is not None and frame==last_action+1:
                assert ram[0x1e54]==skip_page and ram[0x1e68]==ram[0x1e6a],'A should finish text before advancing'
            if frame-since>=10 and ram[0x1e68]==ram[0x1e6a]:
                gid=page['graphics'][key[3]]
                if (key[2],key[3]) not in keys:
                    digest=hashlib.sha256(b''.join(rgb555(p).to_bytes(2,'little') for p in pixels_of(s.image()))).hexdigest()
                    assert digest==manifest['graphic_metrics'][gid]['expected_rgb555_sha256'],('Pixels differ',frame,scene)
                    keys.add((key[2],key[3]));verified.append(dict(scene=scene,page=key[2],choice=key[3],sha256=digest))
                if scene not in ('forest','arrival') and frame-last_action>90:
                    if scene=='fight' and second and not selected:buttons={5};selected=True;last_action=frame
                    elif page['kind']=='ending':finished=True;break
                    else:buttons={8};last_action=frame;skip_page=None
        if ram[0x20]==1 and ram[0x22]==1:
            assert ram[0x1e64]==0 and ram[0x1e66]==0
            if entered is None:
                entered=frame;assert ram[0x500]==(3 if second else 2) and ram[0x700]==(2 if second else 3)
                assert s.memory(45,65536)[0x800:0x840]==driver_prefix,'SB3 SPC driver was not restored'
            if not natural and frame-entered>180:
                hp=0x562 if lose else 0x762;ram[hp]=ram[hp+1]=0
        s.buttons=buttons;s.run()
    assert finished and returned and skipped and len(typewriter_samples)>3
    assert peaks['sb2']>0 and peaks['sb3_battle']>0,peaks
    s.buttons={0};s.run(3);s.buttons=set();s.run(200)
    assert ram[0x20]==6 and ram[0x1e64]==0 and ram[0x1e66]==0,'B did not restore the native title/audio'
    assert s.memory(45,65536)[0x800:0x840]==driver_prefix
    s.close()
    return dict(second=second,lose=lose,natural=natural,frames=frame,verified=verified,audio_peaks=peaks,sb3_spc_restored=True,b_returns_native_menu=True,a_finishes_text_first=True,typewriter_samples=typewriter_samples,rom_sha256=hashlib.sha256(raw).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('core');p.add_argument('rom');p.add_argument('manifest');p.add_argument('--second',action='store_true');p.add_argument('--lose',action='store_true');p.add_argument('--natural',action='store_true');p.add_argument('--out',required=True);a=p.parse_args()
    r=run(a.core,a.rom,a.manifest,a.second,a.lose,a.natural);Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print('First scene passed:',r['frames'],'frames',r['audio_peaks'])
