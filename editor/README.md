## Prélude avec combats (v7)

Ouvrez `prelude_tournoi.json`. Les duels proposent deux combattants natifs,
le choix du camp, une arène et des destinations victoire/défaite. Le lecteur
local permet de simuler le vainqueur. `Construire ROM / IPS` demande votre
ROM française originale de 2 Mio et génère des fichiers séparés.
La ROM obtenue joue de vrais combats, avec des scènes **texte** pour le moment.
Les compositions graphiques SB2 restent dans le projet et ne sont pas exportées
vers la ROM. Le combat prévu dans les bois utilise provisoirement une plaine.
Voir `../docs/campaign-v7.md` pour les essais et limites.

# Atelier scénario SB2 / DBZ3

Desktop Python/Tk editor for 256×224 scenes, transparent character/prop layers,
dialogue and branching choices. It runs locally and requires no account.

## Windows

Install Python 3 with Tcl/Tk support, then in this folder run:

```
py -3 -m pip install -r requirements.txt
py -3 app.py
```

Or double-click `Lancer_editeur.bat` after installing Pillow. This is Python
source, not a compiled EXE. The GUI has been launched and tested under Linux;
Windows launcher and Windows-specific dialogs have not been executed here.

The private downloadable package includes `assets/catalog.json` and its PNGs.
The public repository intentionally contains only code, not the user's ROM,
extracted game artwork or reference screenshots. From the repository, generate
assets using `../tools/extract_sb2_assets.py` or choose an existing catalog.

## Build a scene

1. Load the asset catalog (automatic when `assets/catalog.json` is present).
2. Double-click a background to use it. Double-click any character/prop to add
   a transparent layer. Mix elements from different original scenes.
3. Drag a layer or edit X/Y, size, mirror and layer order in the inspector.
4. Enter dialogue, add named scenes and choose destinations for up to three
   choices per scene. Automatic links and structured combat win/loss links
   are also available. Combat nodes do not launch a game battle in this editor.
5. Set the starting scene. Use the route buttons, Test from beginning and
   View links to inspect the graph. Check links before saving.
6. Save a versioned JSON project or export a composed 256×224 PNG.

Keep the project JSON and referenced assets together when moving a project.
The example project uses `assets/catalog.json` relative to its own folder.
Scene deletion cleans incoming links; loops are permitted. Ctrl+S saves.

## Extraction coverage and limits

The supplied ROM is a modified 4 MiB `SB2 HISTOIRE VERSUS` build, SHA-256
`5563770a1df5a6b1905cad404e32517ff8ed92ab1dc538fb9525a99e4111438a`.
The extraction attempted IDs 00–FF (256 IDs). Runtime checks validated 222
scene initializations; 34 IDs did not reach the expected scene state and were
excluded from the catalog. The verified scenes deduplicated into rendered
resources: 31 background compositions and 35 transparent character/prop
elements. These are the sampled narrative scene resources, not a claim of
all combat animations, all possible poses or every graphic in the ROM.

Backgrounds are captured with the OBJ plane disabled. Characters/props are
rasterized from real 4bpp VRAM tiles, OAM and CGRAM with palette-zero alpha.
The decoder groups nearby connected components, dropping isolated specks
smaller than eight opaque pixels. Overlapping props and characters sometimes
remain combined; these entries are labeled as groups. Special color-math,
window and scanline-limit effects are not baked into sprite PNGs.

Some character names in the delivered catalog were assigned by visual review;
each item retains source scene IDs, origin, OAM provenance and pixel hash.
Generated catalogs from the extractor initially use neutral element labels.
No raw compressed-ROM offsets are falsely presented as verified resources.

## What is not implemented

JSON/PNG export and local route preview work. This editor does not yet encode
SB2 graphics into the SB3 narrative renderer into the ROM. The new campaign compiler inserts scene graphs as text screens
with real battles; it does not compile composed graphics. The v6 IPS retains
the earlier two-route text prologue.
A graphical SNES renderer and a guarded script/asset compiler are still needed
for that next integration step. Keep the editor project as its source of truth.
