# Story Mode integration — experimental prototype

## What is now implemented in source

The prototype builder, tools/build_story_prototype.py, targets the exact French Ultime Menace ROM with SHA-256 `663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`. It writes a separate .sfc and .ips; it never edits the input ROM.

- The title-screen Start transition now targets new global state 13, a self-contained four-choice menu.
- The menu uses an original 5x7 bitmap font and its own 32x32 BG1 tilemaps. It does not depend on guessed original font tile IDs.
- Choices 0-2 seed the original selector variable and jump to the original mode-confirmation routine at BF:AAB7, which performs the game's existing setup before entering state 6/submode 5.
- Choice 3 enters new global state 12, the story screen.
- State 12 has two introductory pages, a two-way choice (help Gohan / follow Vegeta), and two distinct short endings. A restarts the prologue; B returns to the custom menu.
- Story cursor/page/route are volatile WRAM variables at `$7F:FF50`–`$7F:FF52`; no SRAM is added.
- The state tables are relocated to the verified FF-filled area at file offsets `0x1F1806` and `0x1F1830`. Existing initializer entries 0-11 are preserved; state 11 is a special initializer. New states 12 and 13 are appended. The frame table receives a default entry for state 11 plus the new story/menu handlers.

## Important integration details

The original global initializer table has 12 entries (states 0-11), including the special initializer `$81:915B` at index 11. The original per-frame table has 11 entries (states 0-10); state 11 is not a normal frame state. The prototype preserves this distinction rather than overwriting state 11.

The relocated tables are:

- Init table: file `0x1F1806`, CPU `BE:9806`, 14 long pointers for states 0-13.
- Frame table: file `0x1F1830`, CPU `BE:9830`, 14 long pointers for states 0-13.
- Custom code starts at file `0x1F185A`, CPU `BE:985A`.
- Font tiles start at file `0x1F2000`, CPU `BE:A000`.
- Menu/story tilemaps are placed between file `0x1F2400` and `0x1F7400`.

The menu setup calls the complete original submode-2 initializer BF:8104 before drawing the new menu. That routine runs its common initialization tail as well as BF:826D, BF:85FA and BF:874B, so the prototype does not skip the original mode-related setup. It still needs emulator testing.

## Build and verify

```bash
python tools/build_story_prototype.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc" \
  --out-rom build/Ultime-Menace-Story-Prototype.sfc \
  --out-ips build/Ultime-Menace-Story-Prototype.ips \
  --report build/story-prototype-report.json
python -m unittest discover -s tests -v
```

The builder verifies the base hash, original hook bytes, free-space fill, state-table pointers, WRAM address references, output size, checksum/complement and IPS generation. The unit tests cover font/map sizes, menu variants, branch screens, assembler branch ranges and IPS encoding.

## Not yet proven

- The patch has **not** been tested in Mesen, bsnes or another SNES emulator in this environment.
- The menu is a clean text-only prototype, not yet a recreation of Super Butoden 2's visual style.
- The story currently contains dialogue-like pages and branching endings but does not yet launch a battle.
- `$7F:FF50`–`$7F:FF52` have no direct long-address references in the base ROM, but runtime memory use must still be checked.
- PPU register setup, DMA timing, title transition, and the three original mode routes must be tested in an emulator before this is treated as playable.

Do not call this a release patch until these checks pass. The original ROM is never overwritten.
