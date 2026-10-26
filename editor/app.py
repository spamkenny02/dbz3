#!/usr/bin/env python3
"""Desktop scene/branch editor. Run with Python 3 + Pillow, no service required."""
import argparse, json, os, sys, uuid, subprocess, tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from PIL import Image,ImageTk
sys.path.insert(0,str(Path(__file__).resolve().parent))
from model import Assets,compose,actor_image,project,scene,duplicate,save_project,load_project,validate,FIGHTERS,ARENAS,combat_sides,combat_target

ROOT=Path(__file__).resolve().parent

class Editor(tk.Tk):
    def __init__(self,catalog=None,project_path=None):
        super().__init__();self.title('DBZ • Atelier scénario · SB2 v9');self.geometry('1450x900');self.minsize(1160,760)
        self.configure(bg='#13151b');self.data=project();self.assets=None;self.path=None;self.current=0;self.actor=None;self.loading=False;self.dirty=False
        self.ui_font='Segoe UI' if os.name=='nt' else 'DejaVu Sans'
        self.style=ttk.Style(self);self.style.theme_use('clam')
        self.style.configure('.',font=(self.ui_font,10),background='#20232d',foreground='#e5e7ed',fieldbackground='#151821',bordercolor='#343948')
        self.style.configure('TButton',padding=(10,7));self.style.map('TButton',background=[('active','#5740a7')])
        self.style.map('TCombobox',fieldbackground=[('readonly','#151821')],foreground=[('readonly','#e5e7ed')],selectbackground=[('readonly','#453761')],selectforeground=[('readonly','#ffffff')])
        self.style.configure('Treeview',rowheight=28,background='#161922',fieldbackground='#161922',foreground='#e5e7ed')
        self.style.configure('Title.TLabel',font=(self.ui_font,20,'bold'),background='#13151b')
        self.style.configure('Sub.TLabel',foreground='#a6adbd',background='#13151b')
        self.build()
        if project_path:self.open_project(project_path)
        elif catalog:self.load_catalog(catalog);self.seed_demo()
        self.refresh_scenes();self.show_scene(0)
        self.protocol('WM_DELETE_WINDOW',self.quit_editor)
        self.bind('<Control-s>',lambda e:self.save());self.bind('<Control-o>',lambda e:self.open_project())

    def build(self):
        header=ttk.Frame(self,padding=16);header.pack(fill='x')
        ttk.Label(header,text='ATELIER SCÉNARIO',font=(self.ui_font,20,'bold')).pack(side='left')
        ttk.Label(header,text='  DBZ · scènes & embranchements',foreground='#aab0c3').pack(side='left')
        for text,command in [('Enregistrer',self.save),('Ouvrir',self.open_project),('Nouveau',self.new)]:ttk.Button(header,text=text,command=command).pack(side='right',padx=3)
        toolbar=ttk.Frame(self,padding=(16,6));toolbar.pack(fill='x')
        for text,command in [('Charger les assets',self.choose_catalog),('Extraire une ROM SB2',self.extract_rom),('Exporter PNG',self.export_png),('Construire ROM / IPS',self.build_rom),('Vérifier les liens',self.check),('Vue des liens',self.graph),('Tester depuis le début',self.play)]:ttk.Button(toolbar,text=text,command=command).pack(side='left',padx=3)
        nativebar=ttk.Frame(self,padding=(16,4));nativebar.pack(fill='x')
        ttk.Button(nativebar,text='Créer la première scène SB2',command=self.prepare_first_scene).pack(side='left',padx=3)
        ttk.Label(nativebar,text='Musique SB2 · piste :').pack(side='left',padx=(12,4))
        self.music_track=tk.StringVar(value='4');music=ttk.Combobox(nativebar,textvariable=self.music_track,values=[str(i) for i in range(4,22)],state='readonly',width=5);music.pack(side='left');music.bind('<<ComboboxSelected>>',lambda e:self.change_music())
        ttk.Label(nativebar,text='Police originale · texte progressif · scènes fixes',foreground='#aab0c3').pack(side='left',padx=10)
        self.status=tk.StringVar(value='Chargez un catalogue SB2 pour commencer.')
        ttk.Label(self,textvariable=self.status,padding=8).pack(side='bottom',fill='x')
        panes=ttk.Panedwindow(self,orient='horizontal');panes.pack(fill='both',expand=True,padx=12,pady=8)
        left=ttk.Frame(panes,padding=8);center=ttk.Frame(panes,padding=10);right_pane=ttk.Frame(panes,padding=0)
        panes.add(left,weight=2);panes.add(center,weight=5);panes.add(right_pane,weight=3)
        inspector=tk.Canvas(right_pane,bg='#20232d',highlightthickness=0)
        inspector.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(right_pane,orient='vertical',command=inspector.yview);scroll.pack(side='right',fill='y')
        inspector.configure(yscrollcommand=scroll.set)
        right=ttk.Frame(inspector,padding=10);window=inspector.create_window(0,0,window=right,anchor='nw')
        right.bind('<Configure>',lambda e:inspector.configure(scrollregion=inspector.bbox('all')))
        inspector.bind('<Configure>',lambda e:inspector.itemconfigure(window,width=e.width))
        ttk.Label(left,text='RESSOURCES',font=(self.ui_font,11,'bold')).pack(anchor='w',pady=(0,6))
        self.search=tk.StringVar();entry=ttk.Entry(left,textvariable=self.search);entry.pack(fill='x');self.search.trace_add('write',lambda *a:self.refresh_assets())
        self.library=ttk.Treeview(left,show='tree',height=15);self.library.pack(fill='both',expand=True,pady=6);self.library.bind('<Double-1>',lambda e:self.use_asset())
        ttk.Button(left,text='Utiliser la ressource sélectionnée',command=self.use_asset).pack(fill='x')
        ttk.Label(left,text='SCÈNES',font=(self.ui_font,11,'bold')).pack(anchor='w',pady=(18,5))
        self.scenes=ttk.Treeview(left,show='tree',height=7);self.scenes.pack(fill='x');self.scenes.bind('<<TreeviewSelect>>',self.select_scene)
        line=ttk.Frame(left);line.pack(fill='x',pady=5)
        for t,c in [('+',self.add_scene),('Dupliquer',self.copy_scene),('Supprimer',self.delete_scene)]:ttk.Button(line,text=t,command=c).pack(side='left',padx=2)
        ttk.Label(center,text='COMPOSITION · 256 × 224',font=(self.ui_font,11,'bold')).pack(anchor='w')
        ttk.Label(center,text='Glissez un personnage pour le placer. Double-clic sur une ressource pour l’ajouter.',foreground='#aab0c3',wraplength=520).pack(anchor='w',pady=(3,9))
        self.canvas=tk.Canvas(center,width=512,height=448,bg='#0c0d12',highlightthickness=1,highlightbackground='#424657');self.canvas.pack()
        self.canvas.bind('<Button-1>',self.drag_begin);self.canvas.bind('<B1-Motion>',self.drag);self.canvas.bind('<ButtonRelease-1>',lambda e:self.mark())
        self.preview_info=tk.StringVar();ttk.Label(center,textvariable=self.preview_info,foreground='#b4a6e5',wraplength=520).pack(anchor='w',pady=8)
        self.path_buttons=ttk.Frame(center);self.path_buttons.pack(fill='x',pady=8)
        ttk.Label(center,text='Export ROM : décors et personnages fixes, dialogues, choix et combats. 256 couleurs maximum par écran.',foreground='#aab0c3',wraplength=520).pack(anchor='w',pady=10)
        self.name=tk.StringVar();self.kind=tk.StringVar(value='dialogue')
        ttk.Label(right,text='SCÈNE',font=(self.ui_font,11,'bold')).pack(anchor='w')
        ttk.Entry(right,textvariable=self.name).pack(fill='x',pady=5);self.name.trace_add('write',lambda *a:self.change_name())
        kinds=ttk.Combobox(right,textvariable=self.kind,state='readonly',values=['dialogue','choice','combat','ending']);kinds.pack(fill='x');kinds.bind('<<ComboboxSelected>>',lambda e:self.update_scene())
        ttk.Button(right,text='Définir comme point de départ',command=self.set_start).pack(fill='x',pady=5)
        ttk.Label(right,text='Dialogue').pack(anchor='w',pady=(8,2))
        self.dialogue=tk.Text(right,height=4,bg='#151821',fg='#f1e8d9',insertbackground='white',wrap='word',font=(self.ui_font,10));self.dialogue.pack(fill='x');self.dialogue.bind('<KeyRelease>',lambda e:self.update_scene())
        ttk.Label(right,text='PERSONNAGES · calques').pack(anchor='w',pady=(14,4))
        self.actors=tk.Listbox(right,height=4,bg='#151821',fg='#e9e9ef',selectbackground='#58439a',exportselection=False);self.actors.pack(fill='x');self.actors.bind('<<ListboxSelect>>',self.select_actor)
        controls=ttk.Frame(right);controls.pack(fill='x',pady=4)
        self.x=tk.DoubleVar(value=0);self.y=tk.DoubleVar(value=0);self.scale=tk.DoubleVar(value=1);self.z=tk.IntVar(value=0);self.flip=tk.BooleanVar()
        for col,(name,var,low,high,step) in enumerate([('X',self.x,-512,512,1),('Y',self.y,-512,512,1),('Taille',self.scale,.1,4,.1),('Calque',self.z,-99,99,1)]):
            ttk.Label(controls,text=name).grid(row=0,column=col)
            spin=ttk.Spinbox(controls,textvariable=var,from_=low,to=high,increment=step,width=6,command=self.update_actor);spin.grid(row=1,column=col,padx=2);spin.bind('<Return>',lambda e:self.update_actor());spin.bind('<FocusOut>',lambda e:self.update_actor())
        ttk.Checkbutton(right,text='Miroir horizontal',variable=self.flip,command=self.update_actor).pack(anchor='w')
        ttk.Button(right,text='Retirer ce personnage',command=self.delete_actor).pack(fill='x',pady=3)
        ttk.Label(right,text='CHOIX & DESTINATIONS').pack(anchor='w',pady=(14,4))
        self.choice_fields=[]
        for _ in range(3):
            row=ttk.Frame(right);row.pack(fill='x',pady=2)
            label=tk.StringVar();target=tk.StringVar();entry=ttk.Entry(row,textvariable=label,width=17);entry.pack(side='left',fill='x',expand=True)
            combo=ttk.Combobox(row,textvariable=target,state='readonly',width=14);combo.pack(side='left',padx=(4,0))
            entry.bind('<KeyRelease>',lambda e:self.update_scene());combo.bind('<<ComboboxSelected>>',lambda e:self.update_scene());self.choice_fields.append((label,target,combo))
        ttk.Label(right,text='Suite automatique (sans choix)').pack(anchor='w',pady=(6,2))
        self.next=tk.StringVar();self.next_box=ttk.Combobox(right,textvariable=self.next,state='readonly');self.next_box.pack(fill='x');self.next_box.bind('<<ComboboxSelected>>',lambda e:self.update_scene())
        ttk.Label(right,text='COMBAT · joueur / adversaire').pack(anchor='w',pady=(8,2))
        self.player=tk.StringVar();self.opponent=tk.StringVar();row=ttk.Frame(right);row.pack(fill='x')
        for var in (self.player,self.opponent):
            e=ttk.Combobox(row,textvariable=var,values=FIGHTERS,state='readonly',width=14);e.pack(side='left',fill='x',expand=True);e.bind('<<ComboboxSelected>>',lambda e:self.update_scene())
        self.selectable=tk.BooleanVar();self.arena=tk.StringVar(value='plaine_rocheuse')
        ttk.Checkbutton(right,text='Le joueur choisit son combattant parmi les deux',variable=self.selectable,command=self.update_scene).pack(anchor='w')
        ttk.Label(right,text='Arène du combat (décor narratif indépendant)').pack(anchor='w')
        arena_box=ttk.Combobox(right,textvariable=self.arena,values=ARENAS,state='readonly');arena_box.pack(fill='x');arena_box.bind('<<ComboboxSelected>>',lambda e:self.update_scene())
        ttk.Label(right,text='Suite si le joueur gagne / perd').pack(anchor='w')
        self.win=tk.StringVar();self.lose=tk.StringVar();self.win_box=ttk.Combobox(right,textvariable=self.win,state='readonly');self.lose_box=ttk.Combobox(right,textvariable=self.lose,state='readonly')
        for box in (self.win_box,self.lose_box):box.pack(fill='x',pady=2);box.bind('<<ComboboxSelected>>',lambda e:self.update_scene())

    def selected(self):return self.data['scenes'][self.current]
    def mark(self):
        if not self.loading:self.dirty=True;self.title('DBZ • Atelier scénario *')
    def refresh_scenes(self):
        self.loading=True;self.scenes.delete(*self.scenes.get_children())
        self.targets={'— aucune —':None}
        for n,s in enumerate(self.data['scenes']):
            label=f'{n+1:02d} · {s["name"]}';self.targets[label]=s['id']
            self.scenes.insert('', 'end',iid=s['id'],text=('▶ ' if s['id']==self.data['start'] else '')+s['name'])
        values=list(self.targets)
        for _,_,box in self.choice_fields:box.configure(values=values)
        for box in (self.next_box,self.win_box,self.lose_box):box.configure(values=values)
        self.loading=False
    def target_name(self,identifier):return next((label for label,value in self.targets.items() if value==identifier),'— aucune —')
    def select_scene(self,event=None):
        if self.loading:return
        ids=self.scenes.selection()
        if ids:
            index=next(i for i,s in enumerate(self.data['scenes']) if s['id']==ids[0]);self.show_scene(index)
    def show_scene(self,index):
        self.current=index;self.actor=None;self.loading=True;s=self.selected()
        self.name.set(s['name']);self.kind.set(s.get('kind','dialogue'));self.dialogue.delete('1.0','end');self.dialogue.insert('1.0',s.get('dialogue',''))
        for i,(label,target,_) in enumerate(self.choice_fields):
            choice=(s.get('choices',[])+[{}]*3)[i];label.set(choice.get('label',''));target.set(self.target_name(choice.get('target')))
        self.next.set(self.target_name(s.get('next')));combat=s.get('combat',{})
        self.player.set(combat.get('player',''));self.opponent.set(combat.get('opponent',''));self.win.set(self.target_name(combat.get('win')));self.lose.set(self.target_name(combat.get('lose')))
        self.selectable.set(combat.get('selectable',False));self.arena.set(combat.get('arena','plaine_rocheuse'))
        self.loading=False;self.refresh_actors();self.render()
    def change_name(self):
        if self.loading:return
        self.selected()['name']=self.name.get();self.mark()
        sid=self.selected()['id'];self.scenes.item(sid,text=('▶ ' if sid==self.data['start'] else '')+self.name.get())
    def update_scene(self):
        if self.loading:return
        s=self.selected();s['kind']=self.kind.get();s['dialogue']=self.dialogue.get('1.0','end-1c')
        s['choices']=[dict(label=label.get(),target=self.targets.get(target.get())) for label,target,_ in self.choice_fields if label.get().strip() or self.targets.get(target.get())]
        s['next']=self.targets.get(self.next.get());s['combat']=dict(selectable=self.selectable.get(),arena=self.arena.get(),player=self.player.get(),opponent=self.opponent.get(),win=self.targets.get(self.win.get()),lose=self.targets.get(self.lose.get()))
        self.mark();self.render()
    def load_catalog(self,path):
        self.assets=Assets(path);self.refresh_assets();self.status.set(f'{len(self.assets.items)} ressources · {len(self.assets.catalog.get("scenes",[]))} scènes validées · {len(self.assets.catalog.get("errors",[]))} identifiants non couverts')
    def extract_rom(self):
        if getattr(self,'extraction_process',None) is not None:
            messagebox.showinfo('Extraction','Une extraction est déjà en cours.');return
        rom=filedialog.askopenfilename(title='ROM SB2 Tools 4 Mio',filetypes=[('ROM SNES','*.sfc *.smc')])
        if not rom:return
        core=filedialog.askopenfilename(title='Core SNES9X diagnostic (exports CGRAM/OAM)',filetypes=[('Core libretro','*.dll *.so *.dylib'),('Tous','*')])
        if not core:return
        destination=filedialog.askdirectory(title='Dossier du nouveau catalogue')
        if not destination:return
        script=ROOT/'tools/extract_sb2_assets.py'
        if not script.exists():script=ROOT.parent/'tools/extract_sb2_assets.py'
        self.extraction_log=tempfile.TemporaryFile(mode='w+t',encoding='utf-8')
        self.extraction_process=subprocess.Popen([sys.executable,str(script),rom,core,destination],stdout=self.extraction_log,stderr=subprocess.STDOUT)
        def poll():
            self.extraction_log.seek(0);lines=self.extraction_log.read().splitlines()
            self.status.set('Extraction SB2 : '+(lines[-1] if lines else 'initialisation…'))
            if self.extraction_process.poll() is None:self.after(300,poll);return
            code=self.extraction_process.returncode;self.extraction_process=None;self.extraction_log.close()
            if code==0:
                try:self.load_catalog(Path(destination)/'catalog.json');self.render()
                except Exception as error:messagebox.showerror('Catalogue',str(error))
            else:messagebox.showerror('Extraction interrompue','\n'.join(lines[-12:]))
        self.after(300,poll)

    def choose_catalog(self):
        p=filedialog.askopenfilename(filetypes=[('Catalogue JSON','*.json')])
        if p:
            try:self.load_catalog(p);self.mark();self.render()
            except Exception as e:messagebox.showerror('Catalogue',str(e))
    def refresh_assets(self):
        self.library.delete(*self.library.get_children())
        if not self.assets:return
        for kind,label in [('background','Décors'),('sprite','Personnages')]:self.library.insert('','end',iid=kind,text=label,open=True)
        q=self.search.get().casefold()
        for aid,a in self.assets.items.items():
            if q in (a['name']+' '+aid).casefold():self.library.insert(a['kind'],'end',iid=aid,text=a['name'])
    def use_asset(self):
        if not self.assets:return
        ids=self.library.selection()
        if not ids or ids[0] not in self.assets.items:return
        aid=ids[0];a=self.assets.items[aid];s=self.selected()
        if a['kind']=='background':s['background']=aid
        else:
            origin=a.get('origin',[100,40]);s['actors'].append(dict(id=uuid.uuid4().hex[:8],asset=aid,x=origin[0],y=origin[1],scale=1,flip=False,z=len(s['actors'])))
            self.actor=len(s['actors'])-1
        self.refresh_actors();self.mark();self.render()
    def refresh_actors(self):
        self.actors.delete(0,'end')
        for a in self.selected()['actors']:self.actors.insert('end',self.assets.items.get(a['asset'],{}).get('name',a['asset']) if self.assets else a['asset'])
        if self.actor is not None and self.actor<len(self.selected()['actors']):self.actors.selection_set(self.actor);self.load_actor()
    def select_actor(self,e=None):
        ids=self.actors.curselection()
        if ids:self.actor=ids[0];self.load_actor();self.render()
    def load_actor(self):
        a=self.selected()['actors'][self.actor]
        for var,key,default in [(self.x,'x',0),(self.y,'y',0),(self.scale,'scale',1),(self.z,'z',0),(self.flip,'flip',False)]:var.set(a.get(key,default))
    def update_actor(self):
        if self.loading or self.actor is None:return
        try:
            a=self.selected()['actors'][self.actor];a.update(x=round(self.x.get()),y=round(self.y.get()),scale=max(.1,min(4,self.scale.get())),z=self.z.get(),flip=self.flip.get())
            self.mark();self.render()
        except (ValueError,tk.TclError):pass
    def delete_actor(self):
        if self.actor is not None:self.selected()['actors'].pop(self.actor);self.actor=None;self.refresh_actors();self.mark();self.render()
    def drag_begin(self,event):
        if not self.assets:return
        x,y=event.x//2,event.y//2
        for index,a in sorted(enumerate(self.selected()['actors']),key=lambda pair:pair[1].get('z',0),reverse=True):
            im=actor_image(a,self.assets)
            if a['x']<=x<a['x']+im.width and a['y']<=y<a['y']+im.height:
                self.actor=index;self.drag_delta=(x-a['x'],y-a['y']);self.refresh_actors();self.render();return
        self.actor=None;self.render()
    def drag(self,event):
        if self.actor is not None:
            a=self.selected()['actors'][self.actor];a['x']=event.x//2-self.drag_delta[0];a['y']=event.y//2-self.drag_delta[1];self.load_actor();self.render()
    def render(self):
        self.canvas.delete('all');s=self.selected()
        if self.assets:
            try:
                im=compose(s,self.assets);self.photo=ImageTk.PhotoImage(im.resize((512,448),Image.Resampling.NEAREST));self.canvas.create_image(0,0,anchor='nw',image=self.photo)
                if self.actor is not None:
                    a=s['actors'][self.actor];image=actor_image(a,self.assets);self.canvas.create_rectangle(a['x']*2,a['y']*2,(a['x']+image.width)*2,(a['y']+image.height)*2,outline='#c5ff76',width=2)
            except Exception as e:self.status.set(str(e))
        else:self.canvas.create_text(256,224,text='CHARGEZ LE CATALOGUE SB2',fill='#c2b0ee',font=(self.ui_font,14))
        self.preview_info.set(f'{s["name"]} · {len(s["actors"])} personnage(s) · {s.get("kind","dialogue")}')
        for child in self.path_buttons.winfo_children():child.destroy()
        paths=[(c['label'],c.get('target')) for c in s.get('choices',[])]
        if s.get('next'):paths.append(('Continuer →',s['next']))
        if s.get('kind')=='combat':paths.extend([('Simuler victoire joueur',s['combat'].get('win')),('Simuler défaite joueur',s['combat'].get('lose'))])
        for label,target in paths:ttk.Button(self.path_buttons,text=label or '?',command=lambda t=target:self.follow(t)).pack(side='left',padx=2)
    def follow(self,target):
        for index,s in enumerate(self.data['scenes']):
            if s['id']==target:self.show_scene(index);return
        messagebox.showwarning('Destination','Choisissez une scène de destination.')
    def play(self):
        errors=validate(self.data)
        if errors:messagebox.showerror('Projet incomplet','\n'.join(errors));return
        self.play_scene(self.data['start'])
    def play_scene(self,sid,selected=None):
        s=next(s for s in self.data['scenes'] if s['id']==sid)
        win=tk.Toplevel(self);win.title('Lecture du scénario · simulation locale');win.geometry('600x850')
        ttk.Label(win,text=s['name'],font=(self.ui_font,15,'bold')).pack(pady=10)
        if self.assets:
            photo=ImageTk.PhotoImage(compose(s,self.assets).resize((512,448),Image.Resampling.NEAREST))
            label=ttk.Label(win,image=photo);label.image=photo;label.pack()
        ttk.Label(win,text=s.get('dialogue',''),wraplength=550).pack(pady=8)
        def go(target):
            win.destroy()
            if target:self.play_scene(target)
        if s['kind']=='combat':
            c=s['combat']
            if c.get('selectable') and selected is None:
                ttk.Label(win,text='Quel personnage veux-tu incarner ?').pack()
                def choose(fighter):win.destroy();self.play_scene(sid,fighter)
                for fighter in (c['player'],c['opponent']):ttk.Button(win,text=fighter,command=lambda f=fighter:choose(f)).pack()
            else:
                player,opponent=combat_sides(s,selected)
                ttk.Label(win,text=f'Joueur : {player} / CPU : {opponent} · {c.get("arena","plaine_rocheuse")}').pack()
                ttk.Label(win,text='Simulation du résultat uniquement : aucun émulateur lancé.').pack()
                for winner in (player,opponent):
                    ttk.Button(win,text=f'{winner} gagne',command=lambda w=winner:go(combat_target(s,w,selected))).pack()
        elif s.get('choices'):
            for choice in s['choices']:ttk.Button(win,text=choice['label'],command=lambda t=choice['target']:go(t)).pack()
        elif s.get('next'):ttk.Button(win,text='Continuer',command=lambda:go(s['next'])).pack()
        else:ttk.Label(win,text='Fin du parcours').pack()

    def set_start(self):self.data['start']=self.selected()['id'];self.refresh_scenes();self.mark()
    def add_scene(self):self.data['scenes'].append(scene());self.refresh_scenes();self.show_scene(len(self.data['scenes'])-1);self.mark()
    def copy_scene(self):self.data['scenes'].append(duplicate(self.selected()));self.refresh_scenes();self.show_scene(len(self.data['scenes'])-1);self.mark()
    def delete_scene(self):
        if len(self.data['scenes'])==1:return
        sid=self.selected()['id']
        if not messagebox.askyesno('Supprimer','Supprimer cette scène et les liens qui y mènent ?'):return
        self.data['scenes'].pop(self.current)
        for s in self.data['scenes']:
            s['choices']=[c for c in s.get('choices',[]) if c.get('target')!=sid]
            if s.get('next')==sid:s['next']=None
            for k in ('win','lose'):
                if s.get('combat',{}).get(k)==sid:s['combat'][k]=None
        if self.data['start']==sid:self.data['start']=self.data['scenes'][0]['id']
        self.refresh_scenes();self.show_scene(0);self.mark()
    def check(self):
        errors=validate(self.data,self.assets.items if self.assets else None)
        messagebox.showinfo('Vérification','\n'.join(errors) if errors else 'Liens et ressources valides. Les cycles sont autorisés.')
    def graph(self):
        win=tk.Toplevel(self);win.title('Carte des embranchements');win.geometry('900x650')
        c=tk.Canvas(win,bg='#151821',scrollregion=(0,0,900,max(650,len(self.data['scenes'])*140)));c.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(win,orient='vertical',command=c.yview);scroll.pack(side='right',fill='y');c.configure(yscrollcommand=scroll.set)
        positions={s['id']:(40+(i%3)*280,40+(i//3)*180) for i,s in enumerate(self.data['scenes'])}
        for s in self.data['scenes']:
            x,y=positions[s['id']];links=[(ch.get('label',''),ch.get('target')) for ch in s.get('choices',[])]+[('suite',s.get('next'))]
            if s.get('kind')=='combat':links.extend((key,s['combat'].get(key)) for key in ('win','lose'))
            for label,target in links:
                if target in positions:
                    tx,ty=positions[target];c.create_line(x+110,y+60,tx+110,ty,fill='#947de0',arrow='last',width=2);c.create_text((x+tx)//2+110,(y+ty)//2+35,text=label,fill='#c5b8ed')
        for s in self.data['scenes']:
            x,y=positions[s['id']];c.create_rectangle(x,y,x+220,y+60,fill='#302749',outline='#8b73ce');c.create_text(x+110,y+30,text=s['name'],fill='white',width=200)
    def seed_demo(self):
        if not self.assets or not self.assets.catalog.get('scenes'):return
        rows=[r for r in self.assets.catalog['scenes'] if r.get('sprites')]
        if not rows:return
        source=next((r for r in rows if r['id']==2),rows[0]);s=self.selected();s['name']='Un nouveau choix';s['background']=source['background'];s['dialogue']='Le destin de la Terre dépend de notre prochain choix.'
        preferred=[next((a['id'] for a in self.assets.items.values() if a['name']==name),None) for name in ('Gohan','Goku')]
        use_preferred=all(preferred)
        for index,aid in enumerate(preferred if use_preferred else source['sprites']):
            a=self.assets.items[aid];x,y=a.get('origin',[80,40])
            if use_preferred:x,y=(32,168-a['height']) if index==0 else (172,168-a['height'])
            s['actors'].append(dict(id=uuid.uuid4().hex[:8],asset=aid,x=x,y=y,scale=1,flip=bool(use_preferred and index==0),z=len(s['actors'])))
        a=scene('Route Gohan');a['background']=s['background'];a['dialogue']='Rejoindre Gohan pour arrêter le rituel.';a['kind']='ending'
        b=duplicate(a);b['name']='Route Vegeta';b['dialogue']='Suivre Vegeta et découvrir ses intentions.'
        s['kind']='choice';s['choices']=[dict(label='Aider Gohan',target=a['id']),dict(label='Suivre Vegeta',target=b['id'])];self.data['scenes'] += [a,b]
    def guard(self):return not self.dirty or messagebox.askyesno('Modifications','Abandonner les modifications non enregistrées ?')
    def new(self):
        if self.guard():self.data=project();self.path=None;self.current=0;self.refresh_scenes();self.show_scene(0);self.dirty=False
    def open_project(self,path=None):
        if path is None:
            if not self.guard():return
            path=filedialog.askopenfilename(filetypes=[('Projet scénario','*.json')])
        if not path:return
        try:
            data=load_project(path);catalog=(Path(path).resolve().parent/data['catalog']).resolve();self.load_catalog(catalog) if catalog.exists() else setattr(self,'assets',None)
            self.data=data;self.music_track.set(str(data.get('music',{}).get('track',4)));self.path=Path(path).resolve();self.current=0;self.refresh_scenes();self.show_scene(0);self.dirty=False;self.title('DBZ • Atelier scénario')
        except Exception as e:messagebox.showerror('Projet',str(e))
    def save(self):
        self.update_scene()
        path=self.path or filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('Projet scénario','*.json')])
        if not path:return
        try:
            if self.assets:self.data['catalog']=os.path.relpath(self.assets.path,Path(path).resolve().parent)
            save_project(self.data,path);self.path=Path(path).resolve();self.dirty=False;self.title('DBZ • Atelier scénario');self.status.set('Projet enregistré : '+str(path))
        except Exception as e:messagebox.showerror('Enregistrement',str(e))
    def change_music(self):
        if self.loading:return
        if not self.data.get('sb2_style'):
            messagebox.showinfo('Ressources SB2','Créez d’abord la première scène SB2 pour extraire sa police et sa musique.');return
        self.data['music']=dict(source='sb2',track=int(self.music_track.get()));self.mark()
    def prepare_first_scene(self):
        if not self.guard():return
        if self.assets is None:
            self.choose_catalog()
            if self.assets is None:return
        sb2=filedialog.askopenfilename(title='ROM française originale Super Butoden 2 / La Légende Saien (2 Mio)',filetypes=[('ROM SNES','*.sfc *.smc')])
        if not sb2:return
        sb3=filedialog.askopenfilename(title='ROM française originale Butoden 3 / Ultime Menace (2 Mio)',filetypes=[('ROM SNES','*.sfc *.smc')])
        if not sb3:return
        output=filedialog.asksaveasfilename(title='Nouveau projet · première scène SB2',defaultextension='.json',initialfile='Premiere_scene_SB2.json',filetypes=[('Projet JSON','*.json')])
        if not output:return
        script=ROOT/'tools/prepare_first_scene.py'
        if not script.exists():script=ROOT.parent/'tools/prepare_first_scene.py'
        try:
            result=subprocess.run([sys.executable,str(script),sb2,sb3,str(self.assets.path),output,'--track',self.music_track.get()],capture_output=True,text=True)
            if result.returncode:raise ValueError(result.stderr or result.stdout)
            self.dirty=False;self.open_project(output)
            messagebox.showinfo('Première scène prête','Décor, apparitions, police et musique SB2 préparés. Goten est extrait de SB3. Enregistrez puis construisez la ROM avec la ROM SB3 originale.')
        except Exception as error:messagebox.showerror('Préparation SB2',str(error))
    def build_rom(self):
        self.update_scene()
        errors=validate(self.data,self.assets.items if self.assets else None)
        if errors:messagebox.showerror('Projet incomplet','\n'.join(errors));return
        if any(s.get('background') or s.get('actors') for s in self.data['scenes']) and self.assets is None:
            messagebox.showerror('Catalogue manquant','Chargez le catalogue utilisé par les décors et personnages avant de construire.');return
        rom=filedialog.askopenfilename(title='ROM française originale Butoden 3 (2 Mio)',filetypes=[('ROM SNES','*.sfc *.smc')])
        if not rom:return
        output=filedialog.asksaveasfilename(title='Nouvelle ROM (scènes graphiques + combats)',defaultextension='.sfc',filetypes=[('ROM SNES','*.sfc')])
        if not output:return
        if self.path and self.path.resolve() in {Path(output).resolve(),Path(output).with_suffix('.ips').resolve(),Path(output).with_suffix('.json').resolve()}:
            messagebox.showerror('Nom de sortie','Choisissez un autre nom : le rapport de construction ne doit pas remplacer votre projet JSON.');return
        script=ROOT/'tools/build_story_campaign.py'
        if not script.exists():script=ROOT.parent/'tools/build_story_campaign.py'
        try:
            with tempfile.TemporaryDirectory() as d:
                source=Path(d)/'project.json';export_data=json.loads(json.dumps(self.data))
                if self.assets:export_data['catalog']=str(self.assets.path)
                if export_data.get('sb2_style'):
                    candidate=self.assets.root/'sb2_native_style.json' if self.assets else Path('')
                    export_data['sb2_style']=str(candidate.resolve() if self.assets and candidate.is_file() else ((self.path.parent if self.path else ROOT)/export_data['sb2_style']).resolve())
                save_project(export_data,source)
                result=subprocess.run([sys.executable,str(script),rom,str(source),'--out-rom',output,'--out-ips',str(Path(output).with_suffix('.ips')),'--report',str(Path(output).with_suffix('.json'))],capture_output=True,text=True)
                if result.returncode:raise ValueError(result.stderr or result.stdout)
            report=json.loads(result.stdout)
            count=report.get('graphic_variants',0);reduced=sum(m['quantized'] for m in report.get('graphic_metrics',[]))
            messagebox.showinfo('Construction terminée',f'ROM et IPS créés. {count} écran(s) graphique(s) intégré(s).\n{reduced} palette(s) réduite(s) à 256 couleurs.\nLes personnages sont des calques fixes ; le décor du combat est celui de son arène. Testez le parcours dans un émulateur.')
        except Exception as error:messagebox.showerror('Construction',str(error))
    def export_png(self):
        if not self.assets:return
        path=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('Image PNG','*.png')])
        if path:compose(self.selected(),self.assets).save(path);self.status.set('Image 256 × 224 exportée.')
    def quit_editor(self):
        if self.guard():
            process=getattr(self,'extraction_process',None)
            if process is not None:process.terminate()
            self.destroy()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--catalog');parser.add_argument('--project');args=parser.parse_args()
    default=ROOT/'assets/catalog.json';catalog=args.catalog or (str(default) if default.exists() else None)
    Editor(catalog,args.project).mainloop()
