"""Versioned scene graph and deterministic 256x224 scene composition."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json, textwrap, uuid, sys, base64
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 256, 224

# Stable authoring keys; ROM numeric IDs must be verified separately.
FIGHTERS = ('Gohan', 'Goten', 'Vegeta', 'Trunks', 'Goku', 'Trunks (futur)', 'Dabra', 'Majin Buu', 'Petit Buu', 'C18')
ARENAS = ('plaine_rocheuse', 'salle_gravite', 'tournoi')

def combat_sides(s, selected=None):
    """Resolve a real pair, without interpreting the winner as the player."""
    c = s['combat']
    player = selected if c.get('selectable') else c['player']
    pair = (c['player'], c['opponent'])
    if player not in pair: raise ValueError('Personnage hors du duel')
    return player, pair[1] if player == pair[0] else pair[0]

def combat_target(s, winner, selected=None):
    player, opponent = combat_sides(s, selected)
    if winner not in (player, opponent): raise ValueError('Vainqueur hors du duel')
    return s['combat']['win' if winner == player else 'lose']


def scene(name='Nouvelle scène'):
    return dict(id='scene_'+uuid.uuid4().hex[:8],name=name,kind='dialogue',background=None,
                actors=[],dialogue='',choices=[],next=None,combat={'player':'','opponent':'','win':None,'lose':None,'selectable':False,'arena':'plaine_rocheuse'})

def project():
    first=scene('Introduction')
    return dict(format='dbz3-story',version=1,title='Ma saga',start=first['id'],catalog='assets/catalog.json',scenes=[first])

def validate(data,assets=None):
    errors=[]
    if data.get('format')!='dbz3-story' or data.get('version')!=1:return ['Format de projet non pris en charge']
    scenes=data.get('scenes',[]);ids=[s.get('id') for s in scenes]
    if not scenes or len(set(ids))!=len(ids) or any(not x for x in ids):errors.append('Identifiants de scène absents ou dupliqués')
    if data.get('start') not in ids:errors.append('Scène de départ introuvable')
    for s in scenes:
        name=s.get('name',s.get('id','?'))
        for target in [s.get('next')]+[c.get('target') for c in s.get('choices',[])]+[s.get('combat',{}).get(k) for k in ('win','lose')]:
            if target and target not in ids:errors.append(f'{name} : destination {target} introuvable')
        if len(s.get('choices',[]))>3:errors.append(f'{name} : maximum trois choix')
        for choice in s.get('choices',[]):
            if not choice.get('label','').strip() or not choice.get('target'):errors.append(f'{name} : choix incomplet')
        for aid in [s.get('background')]+[a.get('asset') for a in s.get('actors',[])]:
            if aid and assets is not None and aid not in assets:errors.append(f'{name} : ressource {aid} absente')
        if s.get('kind') == 'combat':
            c = s.get('combat', {})
            if c.get('player') not in FIGHTERS or c.get('opponent') not in FIGHTERS:
                errors.append(f'{name} : combattants non reconnus')
            elif c['player'] == c['opponent']:
                errors.append(f'{name} : le duel exige deux personnages distincts')
            if not c.get('win') or not c.get('lose'):
                errors.append(f'{name} : définir les suites victoire et défaite')
            if c.get('arena', 'plaine_rocheuse') not in ARENAS:
                errors.append(f'{name} : arène non reconnue')
            if s.get('choices') or s.get('next'):
                errors.append(f'{name} : le combat utilise uniquement victoire/défaite')
        for actor in s.get('actors',[]):
            if not 0.1<=float(actor.get('scale',1))<=4:errors.append(f'{name} : échelle hors limites')
    return errors

def load_project(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    errors=validate(data)
    if errors:raise ValueError('\n'.join(errors))
    return data

def save_project(data,path):
    errors=validate(data)
    if errors:raise ValueError('\n'.join(errors))
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

class Assets:
    def __init__(self,path):
        self.path=Path(path).resolve();self.root=self.path.parent
        self.catalog=json.loads(self.path.read_text(encoding='utf-8'))
        self.items={a['id']:a for a in self.catalog['assets']};self.cache={}
    def image(self,aid):
        if aid not in self.cache:
            file=(self.root/self.items[aid]['path']).resolve()
            if not file.is_relative_to(self.root):raise ValueError('Asset path outside catalog directory')
            with Image.open(file) as im:self.cache[aid]=im.convert('RGBA')
        return self.cache[aid].copy()

def actor_image(actor,assets):
    im=assets.image(actor['asset']);scale=max(0.1,min(4,float(actor.get('scale',1))))
    im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
    if actor.get('flip'):im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return im

def compose(s,assets,dialogue=True):
    im=Image.new('RGBA',(WIDTH,HEIGHT),(25,0,46,255))
    if s.get('background'):im.alpha_composite(assets.image(s['background']).resize((WIDTH,HEIGHT),Image.Resampling.NEAREST))
    for actor in sorted(s.get('actors',[]),key=lambda a:a.get('z',0)):
        im.alpha_composite(actor_image(actor,assets),(int(actor.get('x',0)),int(actor.get('y',0))))
    if dialogue and s.get('dialogue') and s.get('presentation')=='sb2':
        style=assets.root/'sb2_native_style.json'
        if style.exists():
            toolroot=Path(__file__).resolve().parent/'tools'
            if not toolroot.exists():toolroot=Path(__file__).resolve().parents[1]/'tools'
            sys.path.insert(0,str(toolroot))
            from sb2_style import NativeFont
            font=NativeFont(base64.b64decode(json.loads(style.read_text())['font']))
            lines=[]
            for paragraph in s['dialogue'].replace('’',"'").splitlines():lines.extend(textwrap.wrap(paragraph,26) or [''])
            for n,line in enumerate(lines[:3]):font.draw(im,24,152+n*16,line)
            return im
    if dialogue and s.get('dialogue'):
        draw=ImageDraw.Draw(im)
        candidates=[Path(__file__).with_name('DejaVuSans.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('C:/Windows/Fonts/arial.ttf')]
        font=next((ImageFont.truetype(str(p),11) for p in candidates if p.exists()),ImageFont.load_default())
        lines=[]
        for paragraph in s['dialogue'].splitlines():lines.extend(textwrap.wrap(paragraph,34) or [''])
        for n,line in enumerate(lines[:4]):
            draw.text((8,168+n*13),line,font=font,fill=(248,240,219),stroke_width=1,stroke_fill=(26,4,37))
    return im

def duplicate(s):
    new=deepcopy(s);new['id']='scene_'+uuid.uuid4().hex[:8];new['name']+=' (copie)';return new
