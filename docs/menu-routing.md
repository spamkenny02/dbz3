# Ultime Menace — native menu and Story Mode routing

Status: experimental 4 MiB LoROM patch; static checks pass, but no emulator trace has been run.

## Original ROM identity

- Internal title: DRAGONBALL Z3
- Base size: 2,097,152 bytes (2 MiB)
- SHA-256: 663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa
- Map mode: 0x30 (LoROM/FastROM)
- ROM size code: 0x0B (2 MiB)
- SRAM size byte: 0x00 (no SRAM declared)

## Native menu

The original title Start path at file offset 0x1F9A54 remains A9 06, so the game enters its original state 6 / selector submode 2. The three original labels and background are preserved.

The selector tilemap buffer at $7E:6000 contains four two-row entries, with each entry occupying 0x80 bytes. The first three are COMBAT, CHAMPIONNAT and OPTION; the fourth slot is blank. The patch writes HISTOIRE into that fourth slot using the game's existing 16x16 glyph tiles and palette.

- Label hook: file offset 0x1F878A, replacing JSL $80:883C with JSL C0:8337.
- The wrapper writes 32 tilemap words into $7E:6190 and $7E:61D0, then calls the original $80:883C upload routine.
- The label is centered at columns 8-23.
- Glyph top-left tile IDs are H=0x302, I=0x304, S=0x328, T=0x32A, O=0x320, R=0x326, E=0x2EC. Each glyph uses four 8x8 tiles to form a 16x16 character.
- Unselected tilemap words use the existing palette-3 bits; the original cursor code clears those bits for the selected entry.

## Four-choice input and routing

- Up-wrap operand at 0x1FAB92: A9 02 becomes A9 03.
- Down-limit operand at 0x1FABB1: C9 02 becomes C9 03.
- The existing selector stores the chosen index in $188C.
- At 0x1FAB25, the original A9 06 64 93 sequence calls C0:846E. The helper returns A=6 for indices 0-2 and A=12 for index 3, then the original JML $80:807A state-transition gateway runs.
- State 12 is the branching Story Mode. Story B returns to state 6 / submode 2 and therefore the original menu.

## Expanded ROM tables

The original initializer dispatcher at 80:80D1 uses a 24-bit pointer table at file offset 0xF9 with 12 entries (indices 0-11). The frame dispatcher at 80:82C5 uses a table at 0x2E3 with 11 normal entries (indices 0-10).

| Structure | File offset | CPU address | Entries |
|---|---:|---|---:|
| Init table | 0x200000 | C0:8000 | 14 |
| Frame table | 0x20002A | C0:802A | 14 |
| New code | 0x200054 | C0:8054 | 1,093 bytes |

The original entries are preserved, including the special initializer at state index 11. A default frame entry is added at 11, followed by Story state 12 and the unused development-menu state 13.

The ROM header is changed to size code 0x0C (4 MiB LoROM). The original 2 MiB bytes remain unchanged except for the audited hooks and header/checksum fields. New code/data are stored in the appended banks C0-FF. The old FF-filled range at 0x1F1806-0x1F8000 is not overwritten because static analysis found existing references into it.

## Limitations

- The patch is not emulator-tested; native menu text visibility, PPU/DMA timing, input handling and the three original routes remain to be confirmed.
- The story currently has two intro pages, a two-way choice and two short endings, but does not launch a real battle.
- No SRAM is added. Story variables are volatile WRAM bytes $7F:FF50-$7F:FF52.
