# Native Histoire v3 — tested menu integration

Apply `patches/Ultime-Menace-Native-Histoire-v3.ips` to a fresh French
Ultime Menace ROM (2,097,152 bytes; SHA-256
`663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`).
Do not apply it over v1/v2. Output is 4 MiB. Open under a new filename and
start from reset without loading an old emulator state.

## Root cause and changes

The main title selector uses `$196B`; `$196C` belongs to the COMBAT submenu.
Earlier builds patched the latter. Main selector up/down bounds are now at
ROM `$1FA9ED` and `$1FAA0C`. A tail router at `$BF:A9C9` preserves indices
0–2 and routes index 3 to global state 12 without adding a stack frame.

The map is built in `$7E:6000`. The old initialization hook at `$BF:878A`
ran before that map was built; subsequent work erased the added text.
The new hook at `$BF:AA1A` writes HISTOIRE before the main selector's palette
updates. The length constant at `$BF:AA79` is raised from 2 to 3, extending
DMA from `$0180` to `$0200` bytes at VRAM word address `$5A40`. This includes
all eight tile rows. Font and title artwork remain native.

Emulation exposed additional Story display bugs: BG1SC used the wrong map
address, 2bpp font planes were not interleaved, the native NMI restored stale
PPU shadows, and StoryInit returned with RTL although the state dispatcher
expects the native completion tail at `$80:811D`. These are corrected.

## What was actually tested

The final ROM was executed with the Snes9x 1.61 libretro core from Ubuntu
package `1.61+dfsg-1`. A separately built instrumented Snes9x core traced
DMA sources/destinations and state transitions. Visual inspection confirmed
the native four-entry menu, selected HISTOIRE, introduction and Vegeta ending.

Five deterministic smoke runs (1,801 frames each) cover COMBAT, CHAMPIONNAT,
OPTION, Gohan and Vegeta. Story checks verify pages 0/1/2/3, the route flag,
separate rendered frames and B returning to the native title flow. The three
original menu entries retain their expected native submodes. This does not
constitute a full playthrough of those modes. The 25 Python unit tests pass;
IPS application was independently round-tripped to the final ROM.

Commands (core and commercial ROM must be supplied separately):

```
python3 tools/build_story_prototype.py original.sfc --out-rom build/v3.sfc --out-ips build/v3.ips
python3 tools/smoke_snes9x.py /absolute/path/snes9x_libretro.so build/v3.sfc vegeta
python3 -m unittest discover -s tests -v
```

Exact state/frame results: `docs/snes9x-v3-smoke-results.json`.
The build-only report deliberately keeps `emulator_tested: false`: generating
a new binary does not itself run an emulator. The smoke report records the
hash of the ROM that was actually executed.

## Limits

This remains a text prologue with two routes, without real story battles or
SB2-style scenes. B returns to the native title screen; press A after its
input delay to reopen the menu. No SRAM is added. No commercial ROM or
extracted game graphics are included in the repository.
