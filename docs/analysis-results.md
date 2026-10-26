# Reproducible ROM inspection results

Generated locally with tools/inspect_rom.py and tools/compare_roms.py. The ROM images themselves are not included in this repository.

## Ultime Menace (French)

- File size: 2,097,152 bytes (2 MiB)
- SHA-256: 663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa
- Internal title: DRAGONBALL Z3
- Header offset: 0x7FC0
- Map mode byte: 0x30 (interpreted as LoROM + FastROM)
- SRAM size code: 0x00 (no SRAM declared)
- Region code: 6 (France/Europe)
- Checksum/complement pair: 0xBA6B / 0x4594; XOR pair is valid
- Reset vector: 0xFFA7
- FF-filled runs of at least 0x1000 bytes: 11
- Total bytes inside those reported runs: 229,876 (about 224.5 KiB)

| File offset range (end exclusive) | Length | Canonical LoROM start |
|---|---:|---|
| 0x0059F8–0x007F90 | 9,624 | 80:D9F8 |
| 0x0266F7–0x028000 | 6,409 | 84:E6F7 |
| 0x03EED5–0x040000 | 4,395 | 87:EED5 |
| 0x04ED40–0x050000 | 4,800 | 89:ED40 |
| 0x0555F4–0x058000 | 10,764 | 8A:D5F4 |
| 0x073B00–0x080000 | 50,432 | 8E:BB00 |
| 0x17986B–0x180000 | 26,517 | AF:986B |
| 0x1D849F–0x1E8000 | 64,353 | BB:849F |
| 0x1EB332–0x1F0000 | 19,662 | BD:B332 |
| 0x1F1806–0x1F8000 | 26,618 | BE:9806 |
| 0x1FE762–0x200000 | 6,302 | BF:E762 |

## La Légende Saien (French, reference)

- File size: 2,097,152 bytes
- SHA-256: dd920a8f29dde8712a246a56d28ac0825d15c041d7f77f97dbeb37680751ce68
- Internal title: DRAGONBALL Z 2
- Header offset: 0x7FC0
- Map mode byte: 0x30
- SRAM size code: 0x00
- Region code: 6
- Checksum/complement pair: 0x9042 / 0x6FBD; XOR pair is valid
- Reset vector: 0xFFB7
- FF-filled runs of at least 0x1000 bytes: 1
- Total bytes inside that reported run: 4,634

| File offset range (end exclusive) | Length | Canonical LoROM start |
|---|---:|---|
| 0x1BEDE6–0x1C0000 | 4,634 | B7:EDE6 |

## Comparison

The two files are both 2 MiB, but are not interchangeable ROM revisions. The byte comparison found 1,923,161 differing bytes across 91,104 differing runs. Twenty-five identical runs were at least 256 bytes long. Identical byte ranges may be common routines or data, but must not be labelled as such without disassembly/context.

## Critical caveat about FF runs

An FF-filled range is only a *candidate* for code/data placement. It is not proven unused. Before using any candidate range, inspect all relevant pointers, tables, bank-local addressing, graphics/audio/resource references, and run the game under a debugger/emulator. These numbers must not be treated as a ready-made patch plan.


## Follow-up finding: the apparent FF run is referenced

The FF-filled range `0x1F1806`–`0x1F8000` must not be treated as free space. Static inspection found existing long-indexed reads at file offsets `0x00D561` and `0x00D590` targeting `BE:9806`. The current prototype therefore leaves this range untouched and expands the ROM from 2 MiB to 4 MiB, placing new code/data in the added LoROM banks C0-FF.
