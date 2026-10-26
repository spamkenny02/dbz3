"""Lossless SNES OBJ decoding (4bpp/OAM/CGRAM), independent of screenshots."""
from PIL import Image

SIZES=[((8,8),(16,16)),((8,8),(32,32)),((8,8),(64,64)),
       ((16,16),(32,32)),((16,16),(64,64)),((32,32),(64,64)),
       ((16,32),(32,64)),((16,32),(32,32))]

def color(n):
    return ((n&31)*255//31, (n>>5&31)*255//31, (n>>10&31)*255//31, 255)

def objects(vram, cgram, oam, obsel):
    """Rasterize the visible OBJ plane without blending/windowing/scanline limits.

    Palette index 0 stays transparent. Source OAM indexes are returned for audit.
    This exports source art, not the exact post-color-math screen result.
    """
    palettes=[color(int.from_bytes(cgram[i:i+2],'little')) for i in range(0,512,2)]
    image=Image.new('RGBA',(256,224)); pixels=image.load(); used=[]
    base=(obsel&7)*0x4000; gap=((obsel>>3&3)+1)*0x2000
    for obj in reversed(range(128)):
        x,y,tile,attr=oam[obj*4:obj*4+4]
        hi=(oam[512+obj//4]>>((obj%4)*2))&3
        if hi&1:x-=256
        width,height=SIZES[obsel>>5][hi>>1]
        if y>=224:y-=256
        if x>=256 or x+width<=0 or y>=224 or y+height<=0:continue
        used.append(obj)
        for dy in range(height):
            sy=height-1-dy if attr&0x80 else dy
            for dx in range(width):
                px,py=x+dx,y+dy
                if not (0<=px<256 and 0<=py<224):continue
                sx=width-1-dx if attr&0x40 else dx
                tn=((tile&0xf0)+(sy//8)*16)&0xf0 | ((tile+sx//8)&15)
                address=(base+(gap if attr&1 else 0)+tn*32)&0xffff
                row=sy%8;bit=7-sx%8
                index=sum(((vram[(address+(plane//2)*16+row*2+plane%2)&65535]>>bit)&1)<<plane for plane in range(4))
                if index:pixels[px,py]=palettes[128+(attr>>1&7)*16+index]
    return image, sorted(used)

def split_objects(image):
    """Group nearby alpha components, separating isolated props from actors.

    Deliberately conservative: overlapping objects cannot be unambiguously
    separated from an OAM raster. Original scene/OAM provenance is retained.
    """
    alpha=image.getchannel('A');remaining={(x,y) for y in range(image.height) for x in range(image.width) if alpha.getpixel((x,y))}
    boxes=[]
    while remaining:
        start=remaining.pop();todo=[start];xs=[start[0]];ys=[start[1]]
        while todo:
            x,y=todo.pop()
            for pos in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if pos in remaining:remaining.remove(pos);todo.append(pos);xs.append(pos[0]);ys.append(pos[1])
        boxes.append([min(xs),min(ys),max(xs)+1,max(ys)+1,len(xs)])
    changed=True
    while changed:
        changed=False
        for i,a in enumerate(boxes):
            for j in range(i+1,len(boxes)):
                b=boxes[j];dx=max(0,a[0]-b[2],b[0]-a[2]);dy=max(0,a[1]-b[3],b[1]-a[3])
                if dx<=3 and dy<=5:
                    boxes[i]=[min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3]),a[4]+b[4]];boxes.pop(j);changed=True;break
            if changed:break
    return [(image.crop(tuple(b[:4])),[b[0],b[1]]) for b in sorted(boxes,key=lambda b:(b[0],b[1])) if b[4]>=8]
