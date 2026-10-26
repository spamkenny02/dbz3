"""Offline extraction of native French SB2 fonts and IPL audio packages.
Only extraction recipes/code belong in git; extracted bytes stay private.
"""
import base64,hashlib,json
from pathlib import Path
from PIL import Image
SB2_SHA='dd920a8f29dde8712a246a56d28ac0825d15c041d7f77f97dbeb37680751ce68'

def lorom(pointer):return ((pointer>>16)&127)*0x8000+(pointer&32767)

def decompress(rom,offset):
    size=int.from_bytes(rom[offset:offset+2],'little');at=offset+2;out=bytearray()
    if not 0<size<=65535:raise ValueError('Invalid SB2 compressed size')
    while len(out)<size:
        flags=rom[at];at+=1
        for bit in range(8):
            if len(out)>=size:break
            if flags>>bit&1:out.append(rom[at]);at+=1
            else:
                token=int.from_bytes(rom[at:at+2],'little');at+=2;distance=token>>4
                for _ in range((token&15)+3):out.append(out[-distance] if distance and len(out)>=distance else 0)
    if len(out)!=size:raise ValueError('SB2 decompression exceeded expected size')
    return bytes(out)

def audio_package(rom,command):
    pointer=int.from_bytes(rom[0x26f6+command*3:0x26f9+command*3],'little');at=lorom(pointer)
    data=decompress(rom,at) if command<0x1c else rom[at:]
    blocks=[];pos=0
    while pos+4<=len(data):
        size=int.from_bytes(data[pos:pos+2],'little');dest=int.from_bytes(data[pos+2:pos+4],'little');pos+=4
        if size&0x8000:raise ValueError('Audio package crosses a bank sentinel; unsupported resource')
        if not size:return blocks,dest
        block=data[pos:pos+size]
        if len(block)!=size:raise ValueError('Incomplete audio block')
        blocks.append((dest,block));pos+=size
    raise ValueError('Audio package lacks execution terminator')

FONT_MAP={chr(ord('a')+i):0xe0+i for i in range(26)}
FONT_MAP.update({chr(ord('A')+i):0x1d0+i for i in range(26)})
FONT_MAP.update({str(i):0x1c0+i for i in range(10)})
FONT_MAP.update({' ':0,'.':0x52,',':0x54,"'":0x56,':':0x108,';':0x109,'!':0x148,'?':0x10e,'-':0x10f,
                '>':0x64,'<':0x62,'ê':0xfa,'â':0xfb,'ô':0xfc,'î':0xfd,'û':0xfe,'ë':0xff,'ï':0x100,'ü':0x101,
                'é':0x102,'à':0x103,'è':0x104,'ù':0x105,'œ':0x106,'ç':0x107})
FONT_COLORS=[(0,0,0,0),(213,222,238,255),(57,82,180,255),(123,180,255,255)]

class NativeFont:
    def __init__(self,raw):
        if len(raw)!=16384:raise ValueError('Native SB2 font must be 16 KiB')
        self.raw=raw;self.cache={}
    def glyph(self,char):
        char=char.replace('’',"'")
        if char not in FONT_MAP:raise ValueError(f'Caractère absent de la police SB2 : {char!r}')
        if char not in self.cache:
            k=FONT_MAP[char];tile=k//16*32+k%16;im=Image.new('RGBA',(8,16))
            for y in range(16):
                offset=(tile+(16 if y>=8 else 0))*16+y%8*2
                for x in range(8):
                    value=(self.raw[offset]>>(7-x)&1)|((self.raw[offset+1]>>(7-x)&1)<<1)
                    im.putpixel((x,y),FONT_COLORS[value])
            self.cache[char]=im
        return self.cache[char]
    def draw(self,image,x,y,text):
        for char in text:
            image.paste(self.glyph(char),(x,y),self.glyph(char));x+=8


def extract(rom_path,out_path):
    rom=Path(rom_path).read_bytes()
    if hashlib.sha256(rom).hexdigest()!=SB2_SHA:raise ValueError('Choisissez la ROM française originale SB2 de 2 Mio (La Légende Saien), pas la version Tools modifiée.')
    font=decompress(rom,0x5231)
    packages={}
    for command in [0,1,0x1c]+list(range(4,0x16)):
        blocks,pc=audio_package(rom,command)
        packages[str(command)]=dict(entry=pc,blocks=[dict(destination=d,data=base64.b64encode(b).decode()) for d,b in blocks])
    data=dict(format='sb2-native-style',version=1,source_sha256=SB2_SHA,font=base64.b64encode(font).decode(),font_sha256=hashlib.sha256(font).hexdigest(),audio=packages)
    out=Path(out_path);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');return data

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('output');a=p.parse_args();r=extract(a.rom,a.output);print('Native SB2 style extracted:',len(r['audio']),'audio packages')
