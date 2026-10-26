"""Compile composited 256x224 scenes to SNES Mode 3 8bpp tiles.

Up to 256 RGB555 colors per page. No dithering; preserve exact RGB555 values
when they fit. Quantize only when a composition exceeds the hardware palette.
"""
import hashlib
from PIL import Image, ImageDraw
from build_story_prototype import FONT5X7

SIZE=(256,224)
BLACK=(0,0,0)
WHITE=(255,255,255)
YELLOW=(255,255,0)

def rgb555(rgb):
    r,g,b=rgb[:3]
    return ((r*31+127)//255)|(((g*31+127)//255)<<5)|(((b*31+127)//255)<<10)

def rgb8(n):return tuple(((n>>shift)&31)*255//31 for shift in (0,5,10))

def text(image,x,y,value,color=WHITE):
    draw=ImageDraw.Draw(image)
    for ch in value.upper():
        for row,bits in enumerate(FONT5X7.get(ch,('00000',)*7)):
            for col,bit in enumerate(bits):
                if bit=='1':draw.point((x+col,y+row),fill=color)
        x+=8

def page_image(composition,title,lines,options=(),selected=0,combat=False):
    """Static actor composition with legible, hardware-safe UI colors."""
    image=composition.convert('RGB').copy();draw=ImageDraw.Draw(image)
    draw.rectangle((0,0,255,17),fill=BLACK);text(image,8,5,title[:30],YELLOW)
    if options:
        draw.rectangle((0,144,255,223),fill=BLACK)
        if combat:
            text(image,8,149,'CHOISIS TON COMBATTANT',YELLOW)
            for i,name in enumerate(options):text(image,16,166+i*13,('> ' if selected==i else '  ')+name[:27])
            text(image,8,213,'A:COMBATTRE B:MENU',YELLOW)
        else:
            # Dialogue is paginated separately; final choice page has two lines.
            for i,line in enumerate(lines[:2]):text(image,8,148+i*10,line[:30])
            for i,name in enumerate(options):text(image,8,170+i*12,('> ' if selected==i else '  ')+name[:27])
            text(image,8,213,'A:VALIDER B:MENU',YELLOW)
    else:
        draw.rectangle((0,160,255,223),fill=BLACK)
        for i,line in enumerate(lines):text(image,8,166+i*10,line[:30])
        text(image,8,213,'A:SUITE B:MENU',YELLOW)
    return image

def encode(image):
    if image.size!=SIZE:raise ValueError('SNES scene must be 256x224')
    source=image.convert('RGB');values=[rgb555(p) for p in source.getdata()]
    reserved=[rgb555(c) for c in (BLACK,WHITE,YELLOW)]
    original_colors=len(set(values));quantized=len(set(values)|set(reserved))>256
    if quantized:
        # Reserve exact UI colors after reducing artwork to at most 253 colors.
        rounded=Image.new('RGB',SIZE);rounded.putdata([rgb8(v) for v in values])
        reduced=rounded.quantize(colors=253,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
        rv=[rgb555(p) for p in reduced.getdata()]
        values=[v if v in reserved else rv[i] for i,v in enumerate(values)]
    palette=reserved+sorted(set(values)-set(reserved))
    if len(palette)>256:raise ValueError('Palette exceeds 256 colors')
    lookup={v:i for i,v in enumerate(palette)};indices=bytes(lookup[v] for v in values)
    tiles=[bytes(64)];seen={tiles[0]:0};mapping=[]
    for ty in range(28):
        for tx in range(32):
            tile=bytearray(64)
            for row in range(8):
                for col in range(8):
                    index=indices[(ty*8+row)*256+tx*8+col]
                    for plane in range(8):
                        tile[(plane//2)*16+row*2+plane%2]|=((index>>plane)&1)<<(7-col)
            key=bytes(tile)
            if key not in seen:seen[key]=len(tiles);tiles.append(key)
            mapping.append(seen[key])
    mapping.extend([0]*128)
    tilemap=b''.join(n.to_bytes(2,'little') for n in mapping)
    cgram=b''.join(v.to_bytes(2,'little') for v in palette).ljust(512,b'\0')
    pixels=Image.new('RGB',SIZE);pixels.putdata([rgb8(v) for v in values])
    return dict(tiles=b''.join(tiles),tilemap=tilemap,cgram=cgram,
                metrics=dict(source_rgb555_colors=original_colors,palette_colors=len(palette),
                             quantized=quantized,tiles=len(tiles),
                             expected_rgb_sha256=hashlib.sha256(pixels.tobytes()).hexdigest()),
                expected=pixels)

def decode(tiles,tilemap,cgram):
    """Independent layout decoder for encoder regression and emulator comparison."""
    palette=[rgb8(int.from_bytes(cgram[n:n+2],'little')) for n in range(0,512,2)]
    image=Image.new('RGB',SIZE);pixels=image.load()
    for ty in range(28):
        for tx in range(32):
            at=(ty*32+tx)*2;tile=int.from_bytes(tilemap[at:at+2],'little')&1023
            for y in range(8):
                for x in range(8):
                    n=sum(((tiles[tile*64+(p//2)*16+y*2+p%2]>>(7-x))&1)<<p for p in range(8))
                    pixels[tx*8+x,ty*8+y]=palette[n]
    return image

class Payloads:
    """Allocate appended LoROM bytes without crossing CPU bank DMA boundaries."""
    def __init__(self,start=0x210000,limit=0x400000):
        self.cursor=start;self.limit=limit;self.writes=[];self.cache={}
    def put(self,payload):
        payload=bytes(payload)
        if not payload or len(payload)>0x8000:raise ValueError('Payload must fit a LoROM bank')
        if payload in self.cache:return self.cache[payload]
        if (self.cursor&0x7fff)+len(payload)>0x8000:self.cursor=(self.cursor+0x7fff)&~0x7fff
        offset=self.cursor;self.cursor+=len(payload)
        if self.cursor>self.limit:raise ValueError('Graphismes trop volumineux pour la ROM 4 Mio ; réduisez le nombre de compositions différentes.')
        pointer=((0x80+offset//0x8000)<<16)|(0x8000+(offset&0x7fff))
        self.writes.append((offset,payload));self.cache[payload]=pointer
        return pointer
    def image(self,encoded):
        tiles=encoded['tiles'];segments=[]
        for offset in range(0,len(tiles),0x8000):
            chunk=tiles[offset:offset+0x8000];segments.append((self.put(chunk),len(chunk),offset//2))
        return dict(segments=segments,map=self.put(encoded['tilemap']),palette=self.put(encoded['cgram']),metrics=encoded['metrics'])
    def install(self,rom):
        for offset,payload in self.writes:rom[offset:offset+len(payload)]=payload
