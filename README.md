> **Latest: Native Histoire v3.** Adds HISTOIRE to the original title menu.
> Tested with Snes9x 1.61: native menu, both prologue routes and the three
> original menu entries. [Download IPS](patches/Ultime-Menace-Native-Histoire-v3.ips)
> · [Validation and limits](docs/native-histoire-v3.md).
> Apply to the original French ROM, not an older patched version.

# DBZ3 — Ultime Menace Story Mode Hack

Research, tooling and an experimental branching Story Mode prototype for the French SNES release of Dragon Ball Z 3: Ultime Menace.

## Project rules

- Work from a user-owned ROM. ROM images are not included in this repository.
- Keep the original ROM unchanged; the builder writes a separate .sfc and .ips.
- No SRAM/save feature: route choices and chapter flags live in volatile WRAM only.
- Preserve the original title menu and its three existing choices.
- Static-analysis findings are candidates until runtime-verified.
- The current prototype has not been tested in an emulator and is not a release build.

## Current prototype

- The original title-to-menu flow is preserved.
- The original selector now has a fourth entry, HISTOIRE, placed under OPTION using the original menu glyph tiles and palette.
- Up/Down navigates four entries. The first three keep their original route; confirming HISTOIRE enters Story state 12.
- The story has two introductory pages, a choice between helping Gohan and following Vegeta, and two short endings.
- A advances/restarts the story; B returns to the original three-mode selector.
- Story flags are volatile WRAM only. No SRAM is added.
- The ROM expands from 2 MiB to 4 MiB LoROM; new code/data use appended banks C0-FF, leaving the original FF-filled region with existing references untouched.

## Patch status

The prebuilt IPS binary is not currently included in this repository. Build it locally from the matching French ROM you own using the command below; the ROM itself is not distributed here. The patch remains experimental until its menu rendering and routing are verified in Mesen or bsnes.

## Build from your own ROM

Python 3.10+; standard library only.

    python tools/build_story_prototype.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc" --out-rom build/Ultime-Menace-Native-Histoire.sfc --out-ips build/Ultime-Menace-Native-Histoire.ips --report build/native-story-report.json
    python tools/verify_story_hooks.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc"
    python -m unittest discover -s tests -v

The builder requires the exact French ROM SHA-256 recorded in docs/analysis-results.md. It validates original hook bytes, native-menu patch points, relocated state tables, the 4 MiB header/checksum and IPS reconstruction. See docs/menu-routing.md for the exact selector integration and docs/testing-prototype.md for the emulator checklist.

## Remaining work

- Test the patch in Mesen or bsnes: boot, menu visibility, four-way navigation, confirmation and return.
- Verify PPU/DMA timing and original mode routing under runtime tracing.
- Connect story scenes to real battles and branch on win/loss.
- Add chapters and manga-inspired cutscenes.

## Copyright / distribution

This repository contains original code, documentation and generated UI assets only. Do not commit ROMs, extracted copyrighted graphics/audio, or a complete game image. The IPS patch should be treated as a development build until emulator tests pass.
