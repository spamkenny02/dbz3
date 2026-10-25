# DBZ3 — Ultime Menace Story Mode Hack

Research and tooling for a homebrew ROM patch that adds a replayable, branching Story Mode to the French SNES release of **Dragon Ball Z 3: Ultime Menace**.

## Project rules

- Work from a user-owned ROM. ROM images are not included in this repository.
- Keep the original ROM unchanged; tools write to separate output paths.
- No SRAM/save feature: route choices and chapter flags live in volatile WRAM only. Restarting the story is how players reach other endings.
- Reuse the existing battle engine where possible.
- Do not publish a playable patch until every modified byte is based on a verified hook and the result has been tested in an emulator.
- Static-analysis findings are candidates until runtime-verified.

## Status

- [x] Inspect the supplied French ROM headers and hashes.
- [x] Map top-level state dispatchers and identify a three-position mode-selector candidate.
- [x] Compare the supplied French *La Légende Saien* ROM as a reference for event/script architecture.
- [x] Add byte-level checks for the recorded state tables and selector limits.
- [ ] Confirm visible menu labels and graphics/tilemap data at runtime.
- [ ] Confirm battle start/result/return hooks.
- [ ] Implement the first story-scene prototype.
- [ ] Build and test an IPS/BPS patch.

This repository currently contains diagnostic tooling and design notes, **not a playable hack yet**.

## Quick start

Python 3.10+; standard library only.

```bash
python tools/inspect_rom.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc" --min-fill 4096
python tools/compare_roms.py "path/to/Ultime Menace.sfc" "path/to/La Legende Saien.sfc"
python tools/verify_known_layout.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc"
python -m unittest discover -s tests -v
```

See docs/ for current static-analysis notes and docs/patch-spec-format.md for the guarded IPS format. The known-layout verifier expects the exact ROM SHA-256 documented in docs/analysis-results.md.

## Copyright / distribution

This repository contains analysis code and original documentation only. Do not commit ROMs, extracted copyrighted graphics/audio, or a complete game image. A future patch should be based on a matching user-supplied ROM and only be published after review of its contents and distribution scope.
