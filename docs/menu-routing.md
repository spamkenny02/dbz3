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

## Three-position mode selector candidate

- State-6 submode initializer table at BF:80BC has nine entries: BF:80D7, BF:80E4, BF:8104, BF:8116, BF:8128, BF:813A, BF:8144, BF:815D, BF:8167. Do not append a tenth entry in-place without relocating the table; following bytes are executable code.
- Frame handler BF:A96B dispatches on 25; its 25=2 path enters input handler BF:AB48 after fade completion.
- BF:AB48 checks Up (6D & 0800), Down (6D & 0400), A (6D & 0080), and B (6E & 80). Cursor 196C wraps through 0..2.
- Confirm copies 196C to 188C and sets 1878=5 after a fade. BF:8AE4 later branches on 188C values 0, 1, and 2 to setup/resource paths.
- This is a strong candidate for a fourth Story entry, but visible labels and tilemap data still need runtime confirmation.

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
