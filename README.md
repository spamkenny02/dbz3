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

## Download the current patch

The prebuilt experimental IPS patch is committed at [patches/Ultime-Menace-Native-Histoire.ips](https://github.com/spamkenny02/dbz3/raw/refs/heads/main/patches/Ultime-Menace-Native-Histoire.ips). Its SHA-256 is `479c9f3996955df040d21fb7beda706f73f1dcd614b10c696a93fcadd970773a` (7,414 bytes). The accompanying [validation report](patches/Ultime-Menace-Native-Histoire-Validation.json) records the build checks.

Apply it only to the matching French base ROM (SHA-256 `663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`) using Floating IPS or Lunar IPS. The ROM itself is not included. This is a development patch: native menu rendering and routing still need emulator testing; see [the test checklist](docs/testing-prototype.md).

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
