"""Emit bounded SNES IPL uploads for private SB2 music and SB3 restoration."""
import base64
from sb2_style import lorom
AUDIO_FLAG=0x7e1e64
AUDIO_ERROR=0x7e1e66

def native_sb3_packages(rom):
    packages=[]
    for index in range(4):
        pointer=int.from_bytes(rom[0x3178+index*3:0x317b+index*3],'little');at=lorom(pointer);blocks=[]
        while True:
            size=int.from_bytes(rom[at:at+2],'little')
            if size&0x8000:at=(at+0x8000)&~0x7fff;continue
            dest=int.from_bytes(rom[at+2:at+4],'little');at+=4
            if not size:break
            blocks.append((dest,bytes(rom[at:at+size])));at+=size
        packages.append((blocks,dest))
    return packages

def append_audio(a,pool,style,track,rom):
    """Append to a campaign Asm; callers JSL StartSB2 / RestoreSB3."""
    packages=[]
    for cmd in (0,1,0x1c,track):
        p=style['audio'][str(cmd)];packages.append(([(b['destination'],base64.b64decode(b['data'])) for b in p['blocks']],p['entry']))
    native=native_sb3_packages(rom);counter=[0]
    def tag(prefix):counter[0]+=1;return prefix+str(counter[0])
    def write(addr,value):a.emit(0xa9,value,0x8d,addr&255,addr>>8)
    def wait_echo():
        label=tag('Echo');ok=tag('EchoOK');a.emit(0xa0,0xff,0xff);a.label(label);a.emit(0xcd,0x40,0x21);a.branch(0xf0,ok);a.emit(0x88);a.branch(0xd0,label);a.jml('AudioFail');a.label(ok)
    def wait_ipl():
        label=tag('IPL');ok=tag('IPLOK');a.emit(0xc2,0x20,0xa0,0xff,0xff);a.label(label);a.emit(0xad,0x40,0x21,0xc9,0xaa,0xbb);a.branch(0xf0,ok);a.emit(0x88);a.branch(0xd0,label);a.emit(0xe2,0x20);a.jml('AudioFail');a.label(ok);a.emit(0xe2,0x20)
    def save():
        a.emit(0x08,0x8b,0xc2,0x30,0x48,0xda,0x5a,0xe2,0x20,0xa9,0,0x48,0xab)
        a.lda(0x7e0b43);a.emit(0x48);write(0x4200,0);a.put(0x7e0b43,0);a.put(AUDIO_ERROR,0)
    def upload(packages,first_new):
        # Native drivers keep an IPL clone near 1900, inside the other driver's
        # image. First return to the real SPC boot ROM before replacing it.
        exit_address=0x1928 if first_new else 0x19f1
        packages=[([(0x0800,bytes.fromhex('8f 80 f1 5f c0 ff')),(exit_address,bytes.fromhex('5f 00 08'))],0x0800)]+packages
        for pi,(blocks,entry) in enumerate(packages):
            if pi==0 and first_new:write(0x2140,255)
            else:write(0x2140,255)
            wait_ipl();a.emit(0xa9,0xcc,0x85,6)
            for dest,data in blocks:
                # Resources larger than a LoROM bank are uploaded as contiguous SPC chunks.
                for start in range(0,len(data),0x7000):
                    chunk=data[start:start+0x7000];ptr=pool.put(chunk);destination=dest+start
                    write(0x2142,destination&255);write(0x2143,destination>>8);write(0x2141,1)
                    a.emit(0xa5,6,0x8d,0x40,0x21);wait_echo()
                    loop=tag('AudioByte');a.emit(0xa2,0,0,0xa9,0);a.label(loop)
                    a.emit(0x48,0xbf,ptr&255,ptr>>8&255,ptr>>16,0x8d,0x41,0x21,0x68,0x8d,0x40,0x21);wait_echo()
                    a.emit(0xe8,0x1a,0xe0,len(chunk)&255,len(chunk)>>8);a.branch(0xd0,loop)
                    a.emit(0x1a,0x1a,0x85,6)
            write(0x2142,entry&255);write(0x2143,entry>>8);write(0x2141,0);a.emit(0xa5,6,0x8d,0x40,0x21);wait_echo()
            # Let the uploaded SPC driver reach its command loop.
            a.emit(0xa0,0xff,0xff);pause=tag('AudioPause');a.label(pause);a.emit(0x88);a.branch(0xd0,pause)
            a.emit(0xa0,0xff,0xff);pause=tag('AudioPause');a.label(pause);a.emit(0x88);a.branch(0xd0,pause)
    a.label('StartSB2');save();upload(packages,True)
    a.put(AUDIO_FLAG,1);write(0x2140,1);a.jml('AudioExit')
    a.label('RestoreSB3');a.emit(0x08,0xe2,0x20);a.lda(AUDIO_FLAG);a.emit(0xc9,1);run=tag('RestoreRun');a.branch(0xf0,run);a.emit(0x28,0x6b);a.label(run);a.emit(0x28)
    save();upload(native,False);a.put(AUDIO_FLAG,0)
    for address in (0x40,0x41,0x42,0x49,0x5f):a.put(0x7e0000+address,0)
    for address in range(0x50,0x58):a.put(0x7e0000+address,255)
    a.jml('AudioExit')
    a.label('AudioFail');a.put(AUDIO_ERROR,1);a.put(AUDIO_FLAG,0)
    a.label('AudioExit');a.emit(0x68);a.sta(0x7e0b43);a.emit(0x8d,0,0x42,0xc2,0x30,0x7a,0xfa,0x68,0xab,0x28,0x6b)
    # Gates replace only the three NMI audio call sites, never original routines.
    sites=[]
    for gi,target in enumerate((0x80a982,0x80b0b6,0x80af6f)):
        a.label('AudioGate'+str(gi));a.emit(0x08,0xc2,0x20,0x48,0xe2,0x20);a.lda(AUDIO_FLAG);a.emit(0xc9,1)
        skip=tag('SkipSound');a.branch(0xf0,skip);a.emit(0xc2,0x20,0x68,0x28,0x5c,target&255,target>>8&255,target>>16)
        a.label(skip);a.emit(0xc2,0x20,0x68,0x28,0x6b)
        needle=bytes((0x22,target&255,target>>8&255,target>>16));found=bytes(rom[:0x300]).find(needle)
        if found<0:raise ValueError('Native NMI sound call changed')
        sites.append((found,'AudioGate'+str(gi)))
    return sites
