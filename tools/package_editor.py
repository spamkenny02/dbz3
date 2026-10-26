#!/usr/bin/env python3
"""Package the standalone editor without ROMs or extracted artwork."""
from pathlib import Path
import argparse,zipfile
ROOT=Path(__file__).resolve().parents[1]
TOOLS=('libretro_session.py','snes_graphics.py','extract_sb2_assets.py','build_story_campaign.py','build_story_prototype.py','story_graphics.py','make_ips.py','sb2_style.py','story_audio.py','prepare_first_scene.py','goten_sb3_recipe.json')

def package(output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted((ROOT/'editor').iterdir()):
            if file.is_file():z.write(file,file.name)
        for name in TOOLS:z.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('README.md','snes9x-export.patch'):z.write(ROOT/'emulator-tools'/name,'emulator-tools/'+name)
        doc=ROOT/'docs/first-scene-sb2-v9.md'
        if doc.exists():z.write(doc,'PREMIERE_SCENE_SB2_V9.md')
        z.writestr('DEMARRER.txt','Installez : py -3 -m pip install -r requirements.txt\nCopiez votre dossier assets/ existant a cote de app.py.\nLancez Lancer_editeur.bat puis Creer la premiere scene SB2.\nChoisissez les ROMs FR originales de SB2 (2 Mio) et SB3 (2 Mio), puis sauvegardez le nouveau projet JSON.\nChoisissez la piste musicale SB2, enregistrez et construisez une nouvelle ROM a partir de SB3 originale.\nLes arenes de combat sont independantes des decors de dialogue.\n')
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default=str(ROOT/'releases/Atelier_Premiere_Scene_SB2_v9.zip'));a=p.parse_args();print(package(a.output))
