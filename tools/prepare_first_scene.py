#!/usr/bin/env python3
"""Prepare private SB2 style resources and one complete Gohan/Goten training scene."""
import argparse,hashlib,json,os,sys
from pathlib import Path
from PIL import Image
from sb2_style import extract
from build_story_prototype import BASE_SHA256
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'editor' if (ROOT/'editor/model.py').exists() else ROOT))
from model import scene,save_project

def extract_goten(rom):
    if hashlib.sha256(rom).hexdigest()!=BASE_SHA256:raise ValueError('ROM SB3 française originale requise')
    recipe=json.loads(Path(__file__).with_name('goten_sb3_recipe.json').read_text());image=Image.new('RGBA',(recipe['width'],recipe['height']))
    for obj in recipe['objects']:
        colors=[]
        for i in range(16):
            color=int.from_bytes(rom[obj['palette']+i*2:obj['palette']+i*2+2],'little');colors.append(((color&31)*255//31,(color>>5&31)*255//31,(color>>10&31)*255//31,255 if i else 0))
        for y in range(obj['height']):
            sy=obj['height']-1-y if obj['flip_y'] else y
            for x in range(obj['width']):
                sx=obj['width']-1-x if obj['flip_x'] else x
                off=obj['tiles'][sy//8*(obj['width']//8)+sx//8];row=sy%8;bit=7-sx%8
                n=sum(((rom[off+p//2*16+row*2+p%2]>>bit)&1)<<p for p in range(4))
                if n:image.putpixel((obj['x']+x,obj['y']+y),colors[n])
    return image.crop(image.getbbox())

def prepare(sb2,sb3,catalog_path,output,track=4):
    catalog_path=Path(catalog_path).resolve()
    if Path(output).resolve() in {catalog_path,catalog_path.parent/'sb2_native_style.json'}:raise ValueError('Le nouveau projet doit avoir un nom distinct du catalogue et du style SB2.')
    if not 4<=track<=21:raise ValueError('Piste SB2 attendue entre 4 et 21')
    root=catalog_path.parent;data=json.loads(catalog_path.read_text());items={a['id']:a for a in data['assets']}
    background=next((a['id'] for a in items.values() if a['kind']=='background' and 19 in a.get('source_scenes',[])),None)
    gohan=next((a['id'] for a in items.values() if a['kind']=='sprite' and a.get('name')=='Gohan'),None)
    if not background or not gohan:raise ValueError('Le catalogue SB2 doit contenir Décor scène 13 et Gohan')
    style=root/'sb2_native_style.json';extract(sb2,style)
    sprite=extract_goten(Path(sb3).read_bytes());(root/'images').mkdir(exist_ok=True);sprite.save(root/'images/goten_sb3_standing.png')
    aid='goten_sb3_standing';record=dict(id=aid,kind='sprite',name='Goten · pose SB3 Super Saiyan',path='images/goten_sb3_standing.png',width=sprite.width,height=sprite.height,origin=[180,124],source_sha256=BASE_SHA256)
    data['assets']=[a for a in data['assets'] if a['id']!=aid]+[record]
    backup=catalog_path.with_suffix('.json.bak')
    if not backup.exists():backup.write_bytes(catalog_path.read_bytes())
    catalog_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    actors=[dict(id='gohan',asset=gohan,x=40,y=164-items[gohan]['height'],scale=1,flip=False,z=0),dict(id='goten',asset=aid,x=180,y=164-round(sprite.height*1.4),scale=1.4,flip=False,z=1)]
    scenes=[]
    def add(key,name,text='',cast=2,next=None,kind='dialogue',auto=0):
        s=scene(name);s.update(id=key,presentation='sb2',background=background,actors=actors[:cast],dialogue=text,next=next,kind=kind,auto_frames=auto);scenes.append(s);return s
    add('forest','Les bois',cast=0,next='arrival',auto=45)
    add('arrival','Gohan arrive',cast=1,next='gohan',auto=35)
    add('gohan','Gohan et Goten',"Gohan : Le tournoi a lieu\ndans quelques jours.\nOn doit s'entraîner.",next='goten')
    add('goten','Entraînement',"Goten : D'accord !\nJe vais tout donner !",next='fight')
    s=add('fight','Choix du combattant',kind='combat');s['combat']=dict(player='Gohan',opponent='Goten',selectable=True,arena='plaine_rocheuse',win='win',lose='lose')
    add('win','Victoire',"Bien joué !\nOn progresse tous les deux.",next='end')
    add('lose','Défaite',"Pas mal ! On recommence\nune prochaine fois.",next='end')
    add('end','Fin de scène',"Fin du premier\nentraînement.",kind='ending')
    out=Path(output).resolve();project=dict(format='dbz3-story',version=1,title='Premier entraînement · présentation SB2',start='forest',catalog=os.path.relpath(catalog_path,out.parent),sb2_style=os.path.relpath(style,out.parent),music=dict(source='sb2',track=track),scenes=scenes)
    save_project(project,out);return project

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('sb2');p.add_argument('sb3');p.add_argument('catalog');p.add_argument('output');p.add_argument('--track',type=int,default=4);a=p.parse_args();prepare(a.sb2,a.sb3,a.catalog,a.output,a.track);print('Première scène et ressources préparées')
