# Ultime Menace — menu/state routing

**Status:** static findings only; no ROM bytes changed and no emulator/debugger trace yet. Addresses are SNES CPU addresses unless labelled as file offsets.

## ROM identity

- Internal title: DRAGONBALL Z3
- File size: 2,097,152 bytes
- SHA-256: 663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa
- Map mode byte: 30 (LoROM/FastROM interpretation)
- SRAM size byte: 00 (no SRAM declared)
- Reference La Légende Saien SHA-256: dd920a8f29dde8712a246a56d28ac0825d15c041d7f77f97dbeb37680751ce68

## Main state dispatchers

- State initializer dispatcher: 80:80D1; 24-bit pointer table at 80:80F9.
- Per-frame dispatcher: 80:82C5; pointer table at 80:82E3.
- State transition gateway: 80:807A; target state is written to direct-page 20, previous state to 21.
- Input sampler: 80:85F9; held input words at 69/6B, newly pressed bits at 6D/6F.

Initializer entries relevant to this investigation:

| State | Initializer | File offset | Current interpretation |
|---:|---|---:|---|
| 0 | 81:9018 | 0x009018 | character selection (high confidence) |
| 1 | 87:DD17 | 0x03DD17 | demo/gameplay transition candidate |
| 4 | 81:C2F9 | 0x00C2F9 | secondary interactive screen; exact label unconfirmed |
| 5 | 80:811D | 0x00011D | generic fallback currently; candidate story state after cross-reference checks |
| 6 | BF:8072 | 0x1F8072 | title/menu presentation flow |

## Static Start-to-selector trace

- The title/start input handler BF:9A3C writes `2` to `$1878` when Start is pressed (file offset 0x1F9A47), then returns through the global state dispatcher.
- State-6 submode 2 maps to initializer BF:8104 through the nine-entry submode table at BF:80BC.
- BF:8104 initializes substate 12, calls common setup BF:826D and BF:85FA, then calls BF:874B to load the menu screen resources.
- The selector dispatcher BF:A96B uses `$25` to choose among five handler paths. The mode-selection handler at BF:AA8F jumps to BF:AB48 when `$18A0 == 0`.
- BF:AB48 checks Up (`$6D & $0800`), Down (`$6D & $0400`), A (`$6D & $0080`), and B (`$6E & $80`). Cursor `$196C` currently wraps through 0..2.
- Confirmation copies `$196C` to `$188C` and sets `$1878=5`. The existing setup code expects selection values 0, 1, or 2; a fourth value must branch to a new state before falling into that path.
- This is the strongest static candidate for the mode selector after Start. The visible label/tilemap data still needs to be decoded, and the screen should be confirmed in an emulator before altering its graphics.

## Dedicated-state integration plan

- Preserve all 11 existing global states.
- Relocate the global initializer table and per-frame handler table together into a verified free ROM region, append a twelfth pointer for candidate global state 11, and patch both dispatcher table-base operands.
- Replace the five-byte `A9 05 8D 78 18` sequence at file offset 0x1FAB18 with a four-byte JSL to a router plus NOP. For choices 0..2, the router must reproduce the original `$1878=5` assignment. For choice 3, it should set global state 11; the caller's existing cleanup and dispatcher jump then continue.
- The router source draft is in `asm/selector_router.s`; it is not linked into the ROM yet.
- The FF-filled candidate region at 0x1F1806 is 26,618 bytes, but is not considered safe until resource references and runtime use have been ruled out.

## Candidate code space

A run of FF bytes starts at file offset 1F1806 (LoROM CPU BE:9806) and extends to 1F8000 in the current image. It is **not proven free space** merely because it is filled with FF; pointers, bank-local data, resource references, and runtime execution must be checked before use.

## Story-mode design implications

1. Keep route/chapter/choice flags in volatile WRAM only; no SRAM is requested.
2. Prefer a new state-5 story handler only after verifying state 5 is not used indirectly.
3. Intercept the existing three-choice selector's confirmation path for a fourth entry; add the corresponding menu graphics/tilemap data too.
4. Reuse the original battle setup/result routines only after tracing battle entry and return paths.
5. Do not patch original bytes until instruction boundaries, expected bytes, rationale, and rollback/patch specification are recorded.

## Known limitations

These findings are from static analysis. Runtime screen labels, exact battle transitions, resource decompression, and safe code/data insertion have not been verified in an emulator.
