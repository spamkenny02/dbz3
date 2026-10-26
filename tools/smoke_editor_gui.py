#!/usr/bin/env python3
"""Optional desktop GUI smoke check. Requires a display and a private catalog.
Usage: python tools/smoke_editor_gui.py /path/to/assets/catalog.json
"""
import sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'editor'))
from app import Editor
from model import validate

app=Editor(sys.argv[1]);app.update()
try:
    assert len(app.data['scenes'])==3
    count=len(app.selected()['actors']);assert count
    target=app.selected()['choices'][0]['target'];app.follow(target)
    assert app.selected()['id']==target
    app.show_scene(0)
    sprite=next(a['id'] for a in app.assets.items.values() if a['kind']=='sprite')
    app.library.selection_set(sprite);app.use_asset();assert len(app.selected()['actors'])==count+1
    app.x.set(90);app.y.set(30);app.scale.set(.8);app.flip.set(True);app.update_actor()
    assert app.selected()['actors'][-1]['x']==90
    app.delete_actor();assert len(app.selected()['actors'])==count
    app.add_scene();app.name.set('Scène test');app.update_scene();app.copy_scene()
    assert len(app.data['scenes'])==5
    with patch('app.messagebox.askyesno',return_value=True):app.delete_scene()
    app.show_scene(0)
    with tempfile.TemporaryDirectory() as folder:
        app.path=Path(folder)/'project.json';app.save();assert not app.dirty
        app.open_project(app.path);assert not validate(app.data,app.assets.items)
    app.graph();app.update();app.follow(target);assert app.selected()['id']==target
    print('GUI smoke checks passed')
finally:app.destroy()
