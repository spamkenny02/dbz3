# DBZ3 — Ultime Menace Story Mode

**V8 exports the editor's graphic compositions into the ROM.**
Backgrounds and fixed actor layers, placement, scale, mirror and layer order
are now compiled alongside dialogue, choices and three native battles.
The original Goku/Vegeta intro and native HISTOIRE menu are preserved. No SRAM.

- [Download the graphics editor v8](releases/Atelier_Scenario_GUI_Graphiques_v8.zip)
- [Instructions and limits](docs/campaign-v8-graphics.md)
- [Snes9x evidence](docs/campaign-v8-runtime.json)
- [Forest example project](editor/prelude_decor13.json)
- [Earlier text-only v7 IPS](patches/Ultime-Menace-Histoire-Combats-v7.ips)

Extract the new editor ZIP into a new folder and copy your existing private
`assets/` folder beside `app.py`. Install Pillow, launch `Lancer_editeur.bat`,
open your project and use `Construire ROM / IPS`. Choose the original French
2 MiB ROM and a separate output name. Start the result from reset without an
old emulator state. The completion dialog reports graphic pages exported.

The included `prelude_tournoi.json` has Gohan/Goten training, Vegeta/Trunks
training, Goku's return and the children's final, with player selection and
different win/loss responses. `prelude_decor13.json` sets the forest background
on its first two nodes. Add your own actor layers from the local catalog.
Narrative compositions are static; combat stages still use the selected native
arena. Each composed page supports 256 colors; excess colors are reduced and
reported. Capacity overflow fails the build.

## CLI

Python 3.10+ with Pillow:

```
python -m pip install -r editor/requirements.txt
python tools/build_story_campaign.py original.sfc editor/prelude_decor13.json --out-rom build/story.sfc --out-ips build/story.ips --report build/story.json
python -m unittest discover -s tests -v
python tools/package_editor.py
```

The original ROM must have SHA-256
`663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`.
The compiler resolves the project's catalog relative to its JSON file.

## Distribution

This repository contains code, documentation and JSON examples. Commercial
ROMs and extracted game art stay local. Build the graphical ROM/patch using
your own ROM and private assets. The earlier v6/v7 patches remain archived;
they do not gain graphic support without rebuilding through the new compiler.
