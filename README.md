# DBZ3 — Ultime Menace Story Mode Hack

Research, tooling and an **experimental text-only branching Story Mode prototype** for the French SNES release of **Dragon Ball Z 3: Ultime Menace**.

## Project rules

- Work from a user-owned ROM. ROM images are not included in this repository.
- Keep the original ROM unchanged; the builder writes a separate .sfc and .ips.
- No SRAM/save feature: route choices and chapter flags live in volatile WRAM only.
- Preserve the three original game modes and reuse the original battle engine where possible.
- Static-analysis findings are candidates until runtime-verified.
- The current prototype has **not** been tested in an emulator and is not a release build.

## Current prototype

- Start from the title screen enters a custom four-choice menu.
- The first three options return to the original mode-confirmation routine.
- The fourth option opens a dedicated story state with two intro pages, a two-way choice, and two different short endings.
- A restarts the story; B returns to the custom menu.
- The UI uses a small original bitmap font and custom tilemaps; no copyrighted game assets are included in the repository.
- Story variables are volatile WRAM only; no SRAM is added.

## Build from your own ROM

Python 3.10+; standard library only.

```bash
python tools/build_story_prototype.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc" \
  --out-rom build/Ultime-Menace-Story-Prototype.sfc \
  --out-ips build/Ultime-Menace-Story-Prototype.ips \
  --report build/story-prototype-report.json
python tools/verify_story_hooks.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc"
python -m unittest discover -s tests -v
```

The builder requires the exact French ROM SHA-256 recorded in docs/analysis-results.md. It validates original hook bytes, candidate free space, relocated state tables, output checksum and IPS generation. See docs/integration-next-steps.md for addresses and limitations, and docs/testing-prototype.md for the emulator test checklist.

## Remaining work

- Emulator-test menu navigation, PPU/DMA setup and original mode routing.
- Confirm the WRAM allocation under runtime tracing.
- Connect story scenes to a real battle and branch on win/loss.
- Add more chapters and improve the UI to match the original game's presentation.

## Copyright / distribution

This repository contains original code, documentation and a generated bitmap font only. Do not commit ROMs, extracted copyrighted graphics/audio, or a complete game image. The IPS patch should be built from the user's exact ROM and only published as a release after emulator testing.
