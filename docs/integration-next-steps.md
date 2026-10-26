# Story Mode integration — native-menu prototype

## What is implemented

The builder tools/build_story_prototype.py targets the exact French Ultime Menace ROM with SHA-256 663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa. It writes a separate 4 MiB ROM and IPS patch; the original file is never overwritten.

- The original title Start path is preserved and still enters global state 6 / selector submode 2.
- The existing selector receives a fourth label, HISTOIRE, below OPTION. It uses the original 16x16 glyph tiles and menu palette, not a replacement black menu.
- The selector's wrap/limit values change from 2 to 3, allowing indices 0-3.
- The original confirmation path still handles indices 0-2. At the final state transition, index 3 selects new global state 12.
- Story state 12 shows two intro pages, a two-way choice (help Gohan / follow Vegeta), and two short endings. A advances/restarts; B returns to the original selector.
- Story cursor/page/route are volatile WRAM bytes at $7F:FF50-$7F:FF52; no SRAM is added.
- The ROM expands from 2 MiB to 4 MiB LoROM. New code and data live in the appended banks C0-FF.

The previous custom four-choice menu state (state 13) remains in the development code but is no longer used by the normal title/menu path.

## Native menu integration points

- Title-to-selector path: file offset 0x1F9A54 remains A9 06.
- Original PPU/DMA call at file offset 0x1F878A is wrapped by NativeMenuAddStory at C0:8337; the wrapper writes HISTOIRE into the fourth menu slot, then calls the original $80:883C routine.
- The selector input handler's Up wrap at 0x1FAB92 changes from A9 02 to A9 03.
- The Down limit at 0x1FABB1 changes from C9 02 to C9 03.
- At file offset 0x1FAB25, the original LDA #$06 / STZ $93 pair is replaced by a call to StorySelectState at C0:846E. It returns state 6 for choices 0-2 or state 12 for HISTOIRE, then the original state-transition gateway runs.
- Story B uses StoryReturnToNativeMenu at C0:8483 to restore selector submode 2 before returning to state 6.

The menu tilemap buffer at $7E:6000 reserves four two-row entries. HISTOIRE uses the fourth slot at byte offsets $0190 and $01D0 (starting at column 8), with the existing menu's 16x16 glyph tiles and unselected palette. The selector's existing palette update then highlights it when index 3 is selected.

## ROM layout

- Init table: file offset 0x200000, CPU C0:8000, 14 entries (states 0-13).
- Frame table: file offset 0x20002A, CPU C0:802A, 14 entries.
- New code: file offset 0x200054, CPU C0:8054, 1,093 bytes in the current build.
- Native-menu label hook routine: C0:8337.
- Story selection router: C0:846E.
- Story return-to-native-menu routine: C0:8483.
- Story font and custom story tilemaps remain in appended ROM space at 0x201000 and 0x204000-0x206800.

The original 12 initializer entries (states 0-11) are preserved, including the special initializer at index 11. The original 11 frame entries (states 0-10) are preserved; a default handler is appended at 11, then story and development-menu handlers at 12 and 13.

## Build and test

    python tools/build_story_prototype.py "path/to/Dragon Ball Z - Ultime Menace (France).sfc" --out-rom build/Ultime-Menace-Native-Histoire.sfc --out-ips build/Ultime-Menace-Native-Histoire.ips --report build/native-story-report.json
    python -m unittest discover -s tests -v

The builder checks the exact base hash, original hook bytes, native-menu patch points, reserved WRAM references, state pointers, 4 MiB size header, checksum/complement and IPS generation. Unit tests cover the assembled code, glyph tile values, tilemaps and IPS expansion.

## Not yet proven

- The patch has not been run in Mesen, bsnes or another SNES emulator in this environment.
- The native menu overlay hook is statically placed before the original PPU/DMA call, but actual label visibility and timing still need runtime confirmation.
- The new selector route and original three choices need emulator testing.
- Story Mode does not launch a real battle yet.
- WRAM allocation, 4 MiB LoROM mapping, PPU/DMA timing and controller input must be runtime-verified before release.

Do not call this a release patch until those tests pass.
