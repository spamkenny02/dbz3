# Native Histoire v4 — direct startup, Story first

The title menu now opens automatically after resource initialization, without
playing the Goku/Vegeta intro or waiting for Start/A. The native title backdrop
and its static character artwork remain. Menu order and default selection:

1. HISTOIRE (selected)
2. COMBAT
3. CHAMPIONNAT
4. OPTION

B in Story initializes this same menu again, with HISTOIRE selected.

## Implementation

Boot-state byte at ROM `$7F90` selects state 13. Its new DirectMenuInit handler
prepares native submode-2 resources using `$BF:826D`, `$BF:85FA` and `$BF:874B`,
then starts the original main-menu transition (state `$23=0A`, `$24=04`,
`$25=00`). Initialization finishes through `$BF:8171`.

The overlay reconstructs the three original entries from the decompressed
map at `$7E:80C0` into `$7E:6080`, then draws HISTOIRE in the first slot. This
avoids shifting already shifted rows each frame. NativeMainConfirm routes
index 0 to Story, and indices 1–3 to native submodes 2–4. The hook's 24-bit
target now derives all address bytes from the same label.

## Validation

Snes9x 1.61 libretro: five runs of 901 frames, covering Gohan, Vegeta, COMBAT,
CHAMPIONNAT and OPTION. Each run asserts that the main menu is already active
with cursor 0 at frame 220, before any controller event. The Story runs also
check the introduction, choice, endings and B returning to the menu with
cursor 0. Original mode routing remains intact; no full playthrough of those
modes is claimed. Visual inspection confirmed the new menu order and default
highlight. All 25 unit tests pass. IPS application reproduces the tested ROM
byte for byte. Exact hashes and state/frame checks are in
`snes9x-v4-smoke-results.json`.

```
python3 tools/build_story_prototype.py original.sfc --out-rom build/v4.sfc --out-ips build/v4.ips
python3 tools/smoke_snes9x.py /path/snes9x_libretro.so build/v4.sfc gohan
python3 -m unittest discover -s tests -v
```

Apply the v4 IPS to a fresh French 2 MiB ROM, SHA-256
`663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`.
Do not apply it over v3 or load an old emulator state. Output is 4 MiB.
This remains a two-route text prologue without real Story battles or SRAM.
