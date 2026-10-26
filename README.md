# DBZ3 — Ultime Menace Story Mode

**V7: a modifiable tournament prelude with three native battles.**
Original Goku/Vegeta introduction and native HISTOIRE menu are preserved.
No SRAM: choices and progress last only for the current session.

- [Download v7 IPS](patches/Ultime-Menace-Histoire-Combats-v7.ips)
- [Download updated Windows/Python editor](releases/Atelier_Scenario_GUI_Combats_v7.zip)
- [Editable sample campaign](editor/prelude_tournoi.json)
- [Validation and limits](docs/campaign-v7.md)
- [Snes9x runtime evidence](docs/campaign-v7-runtime.json)

Apply the patch to your **original French 2 MiB ROM**, never an older patched
version. Boot without an old save state. Output is 4 MiB. V6 remains available
in `patches/` for comparison.

## Campaign

1. Gohan/Goten training, choose either fighter, different win/loss dialogue.
2. Vegeta/Trunks training, choose either fighter, both outcomes continue.
3. Goku's return, then Goten/Trunks children's final, choose either fighter.

Current ROM cutscenes are **text screens**. The editor's SB2 compositions are
not yet compiled into the SNES renderer. The intended woods duel temporarily
uses the native rocky plain; gravity room and tournament use native terrains.
Bulma, Chichi and Piccolo appear in dialogue, not new cutscene sprites.

## Desktop editor

Extract the editor ZIP into a new folder and copy your existing private
`assets/` folder alongside `app.py`. No commercial artwork is included here.

```
py -3 -m pip install -r requirements.txt
```

Double-click `Lancer_editeur.bat`. It opens `prelude_tournoi.json` by default.
Select a combat scene to set fighters, player selection, arena and the two
result destinations. `Tester depuis le début` simulates results locally.
`Construire ROM / IPS` builds a separate playable ROM and IPS using your
original French ROM. [Editor instructions](editor/README.md).

## Build and check from the repository

Python 3.10+ with Pillow:

```
python -m pip install -r editor/requirements.txt
python tools/build_story_campaign.py original.sfc editor/prelude_tournoi.json --out-rom build/prelude.sfc --out-ips build/prelude.ips --report build/prelude.json
python -m unittest discover -s tests -v
```

The builder requires SHA-256
`663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`.
It validates the original hook and writes separate outputs. Runtime tests
cover all three battles, both choices and both result branches, plus a full
natural CPU-win route. The outcome-coverage runs use injected KOs, explicitly
recorded in the evidence. Original mode routing and sampled intro frames
were checked as well.

The earlier menu-only builder is retained as `tools/build_story_prototype.py`.

## Distribution

The repository contains code, documentation and patches. Do not commit ROMs,
extracted commercial graphics/audio or complete game images. Private SB2 assets
stay local. Original ROMs must remain untouched.
