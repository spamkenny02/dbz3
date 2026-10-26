#!/usr/bin/env python3
"""Package the standalone editor without ROMs or extracted artwork."""
from pathlib import Path
import argparse,zipfile
ROOT=Path(__file__).resolve().parents[1]
TOOLS=('libretro_session.py','snes_graphics.py','extract_sb2_assets.py','build_story_campaign.py','build_story_prototype.py','story_graphics.py','make_ips.py')

def package(output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted((ROOT/'editor').iterdir()):
            if file.is_file():z.write(file,file.name)
        for name in TOOLS:z.write(ROOT/'tools'/name,'tools/'+name)
        for name in ('README.md','snes9x-export.patch'):z.write(ROOT/'emulator-tools'/name,'emulator-tools/'+name)
        doc=ROOT/'docs/campaign-v8-graphics.md'
        if doc.exists():z.write(doc,'GRAPHIQUES_V8.md')
        z.writestr('DEMARRER.txt','Installez : py -3 -m pip install -r requirements.txt\nCopiez votre dossier assets/ existant a cote de app.py.\nLancez Lancer_editeur.bat et ouvrez votre projet JSON.\nLes decors et personnages fixes sont maintenant exportes dans la ROM.\nConstruire ROM / IPS demande la ROM francaise originale de 2 Mio.\nLes arenes de combat sont independantes des decors de dialogue.\n')
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default=str(ROOT/'releases/Atelier_Scenario_GUI_Graphiques_v8.zip'));a=p.parse_args();print(package(a.output))
