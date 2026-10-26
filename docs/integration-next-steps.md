# Story Mode integration — experimental prototype

## What is implemented

The prototype builder, `tools/build_story_prototype.py`, targets the exact French Ultime Menace ROM with SHA-256 `663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`. It writes a separate 4 MiB ROM and IPS patch; it never edits the input ROM.

- The title-screen Start transition enters new global state 13, a self-contained four-choice menu.
- The menu uses an original 5x7 bitmap font and custom 32x32 BG1 tilemaps.
- Choices 0-2 seed the original selector variable and jump to BF:AAB7, the original mode-confirmation routine.
- Choice 3 enters new global state 12, the story screen.
- State 12 has two introductory pages, a two-way choice (help Gohan / follow Vegeta), and two short endings. A restarts the prologue; B returns to the custom menu.
- Story cursor/page/route are volatile WRAM variables at `$7F:FF50`–`$7F:FF52`; no SRAM is added.
- The image is expanded from 2 MiB to 4 MiB. New code and data live in the standard LoROM upper half, banks C0-FF.

## Why the earlier FF region is no longer used

The original FF-filled range at file offsets `0x1F1806`–`0x1F8000` is not safe to overwrite. Static inspection found existing long-indexed reads targeting `BE:9806` from code at file offsets `0x00D561` and `0x00D590`. The prototype now avoids that range entirely and uses appended ROM banks instead.

## New layout

- Init table: file `0x200000`, CPU `C0:8000`, 14 long pointers for states 0-13.
- Frame table: file `0x20002A`, CPU `C0:802A`, 14 long pointers for states 0-13.
- Custom code: file `0x200054`, CPU `C0:8054`, 743 bytes in the current build.
- Story init/frame: `C0:8054` / `C0:806C`.
- Menu init/frame: `C0:8150` / `C0:816E`.
- PPU/DMA renderer: `C0:822E`.
- Font tiles: file `0x201000`, CPU `C0:9000`.
- Menu/story tilemaps: file offsets `0x202000` through `0x206800` (each 0x800 bytes).

The original 12 initializer entries (states 0-11) are preserved, including the special initializer at index 11. The original 11 frame entries (states 0-10) are preserved; a default entry is added at 11, then states 12 and 13 are appended. Both dispatcher table-base operands are redirected to the new tables in bank C0.

## Build and verify

```bash
python tools/build_story_prototype.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc" \
  --out-rom build/Ultime-Menace-Story-Prototype.sfc \
  --out-ips build/Ultime-Menace-Story-Prototype.ips \
  --report build/story-prototype-report.json
python -m unittest discover -s tests -v
```

The builder validates the exact base hash, original hook bytes, reserved WRAM address references, table pointers, output size code, checksum/complement, and IPS expansion. Unit tests cover font/map sizes, menu variants, branch screens, assembler branch ranges, and IPS expansion.

## Not yet proven

- The patch has **not** been tested in Mesen, bsnes or another SNES emulator in this environment.
- The menu is text-only and does not yet match Super Butoden 2's original presentation.
- The story currently contains dialogue-like pages and branching endings but does not yet launch a battle.
- The WRAM bytes have no direct long-address references in the base ROM, but runtime memory use must still be checked.
- The 4 MiB LoROM mapping, PPU register setup, DMA timing, title transition and original mode routes must be tested before this is treated as playable.

Do not call this a release patch until those tests pass. The original 2 MiB ROM is never overwritten.
