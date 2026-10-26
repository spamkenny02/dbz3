# V8 — compositions from the editor displayed in the ROM

The campaign compiler now exports selected backgrounds and actor layers,
including X/Y, scale, horizontal mirror and layer order. These are static
compositions. Native battles, player selection, outcome branches and the
original intro/menu remain in place. No SRAM is added.

## Windows use

1. Extract `Atelier_Scenario_GUI_Graphiques_v8.zip` into a new folder.
2. Copy your existing `assets/` folder beside `app.py`. It must contain the
   catalog JSON and its referenced images. Keep your authored project JSON.
3. Launch `Lancer_editeur.bat`, open your project and check its composition.
   Load the correct catalog if your project moved. The optional
   `prelude_decor13.json` selects the extracted forest on the first two nodes.
4. Choose `Construire ROM / IPS`, select the **original French 2 MiB ROM**,
   then choose a new output filename. The ROM, IPS and JSON build report are
   written separately. Never patch an older patched ROM.
5. The completion dialog reports graphical screens included and palettes
   reduced. Boot the new ROM from reset without an older emulator state.

The export uses an absolute catalog path in its temporary project, so moving
that temporary JSON does not lose the user's asset references. Missing catalogs,
unknown asset IDs and absent images fail the build instead of silently dropping
compositions. Output paths must differ from inputs; the GUI also protects the
author's JSON project from being replaced by the JSON build report.

## Palette and screen conversion

The editor renders a 256x224 composition. The compiler converts it into SNES
Mode 3 BG1 data: 8bpp planar tiles, a 32x32 tilemap and 512-byte RGB555 CGRAM.
The whole scene is flattened, so separate actor palettes do not conflict.
Source RGB555 colors are preserved exactly if the composite plus UI fits in
256 colors. Otherwise the compiler reduces colors without dithering and records
`quantized: true` in `graphic_metrics`; the GUI reports that count. Size alone
does not guarantee a palette will fit when combining many different scenes.

Title and dialogue/choice panels cover part of the composition. Dialogue pages
show four lines; choices can get a separate final page so dialogue is not lost.
Artwork and actor coordinates otherwise retain their editor positions. The
prototype font still transliterates French accents to ASCII.

This is a static graphical story renderer, not SB2's original scene animation
interpreter. Actors remain fixed within a page. Narrative backgrounds do not
replace native combat stages: the combat node's `arena` still determines the
fight terrain.

## Memory and DMA

Campaign code uses appended bank C1. Deduplicated tilemaps, palettes and tile
payloads share a bank-safe allocator from file offset 0x210000. A transfer never
crosses a LoROM CPU bank boundary. Tile sets above 512 tiles use two transfers.
BG1 tiles start at VRAM byte 0; its map starts at byte F000. The maximum bitmap
has 897 tiles including the blank tile, below that map address.

Rendering disables NMI during forced blank, uploads tiles/map/CGRAM, updates
the native PPU shadows, and restores NMI/display. BG1 vertical scroll is -1 to
match bitmap row zero to the first visible scanline. Story data continues to use
volatile WRAM 7E:1E54–1E62. Builds reject ROM/data/code capacity overflow rather
than overwriting original banks. This version still targets 4 MiB LoROM.

## Verification

See `campaign-v8-runtime.json`. Snes9x libretro upstream 1bcc369 was used.
The forest named **Décor scène 13** is `background_0012` in the supplied catalog.
Its graphic conversion uses no palette reduction. A composition with Gohan and
Goku was used specifically to test transparency, actor placement, scale/mirror
and z order; it is a renderer fixture, not a change to the requested cast.

Tests cover a campaign with graphics on all dialogue, choice-of-fighter,
win/loss and ending screens. The runtime harness compares RGB555 pixel hashes
to the compiler's expected images after each stable page. Both fighter choices
and both outcome paths are exercised. Outcome-coverage tests inject KOs; an
additional complete run uses natural CPU wins. A mixed graphical/text campaign
checks switching to the legacy text renderer. A 619-tile synthetic image checks
two-bank DMA with an exact pixel comparison. Original mode routing and sampled
intro frames are checked separately.

The updated GUI was exercised on Linux/Tk under Xvfb, including asset catalog
resolution through the temporary export project, transformed layers, ROM/IPS
build, CLI equality and project-overwrite protection. The standalone ZIP is
extracted to a path with spaces and accents for an independent full build.
The new Windows version itself was not executed here.

Extracted game artwork and ROMs remain local. The public ZIP contains the
compiler/editor and JSON examples, not commercial assets or a full game image.
