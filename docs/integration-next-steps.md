# Story Mode integration — next verified steps

## Why the next patch is not yet emitted

The selector hook at BF:AB48 (file offset 0x1FAB48) is a real input routine with three-position wrap limits at 0x1FAB92 and 0x1FABB1. However, it is reached through state-6 substate 12, and three different state-6 initializers set that same substate while loading different screen resources. Therefore, static analysis has not yet proved which of those screens is the top-level mode menu shown on a fresh boot.

The title/menu flow also uses state-6 substate 6 (handler BF:9D02), whose cursor logic uses a different variable (0x187E) and an eight-step limit. Adding a fourth choice to BF:AB48 before identifying the exact user-facing screen could modify the wrong menu. This is a blocking integration question, not a reason to guess.

## Verified exact-ROM facts

The supplied Ultime Menace ROM is 2 MiB, SHA-256 `663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`, internal title `DRAGONBALL Z3`, and SRAM-size byte 0.

| Purpose | File offset | Current bytes |
|---|---:|---|
| Up-wrap limit in BF:AB48 | `0x1FAB92` | `A9 02` |
| Down limit in BF:AB48 | `0x1FABB1` | `C9 02` |
| Copy selector cursor to selected-mode variable | `0x1FAAF6` | `AD 6C 19 8D 8C 18` |
| Set state-6 submode 5 after selection | `0x1FAB18` | `A9 05 8D 78 18` |
| Return to state dispatcher | `0x1FAB32` | `5C 7A 80 80` |

The top-level global-state init table currently has 11 entries at file offset `0xF9`; the per-frame handler table has 11 entries at `0x2E3`. Each entry is a 24-bit long pointer, and the dispatcher indexes each table by `state * 3`.

## Candidate clean integration architecture

1. Identify the exact screen/entry point from a fresh boot, ideally by an emulator screenshot and trace or a debugger breakpoint at BF:AB48 and BF:9D02.
2. Preserve the original 11 global states. If a dedicated state is needed, relocate both pointer tables into verified free ROM space, append a new state entry (candidate state 11), and patch both table-base operands in the dispatchers.
3. Add a selector router only at the confirmed mode-selection screen. Existing choices must retain their current behavior; the new choice should set global state 11 and use the normal dispatcher.
4. Allocate volatile story flags only after WRAM usage is audited. No SRAM or persistent saves are planned.
5. Identify the existing text/portrait rendering path before implementing the first dialogue scene.
6. Connect a single existing battle only after the battle-entry and battle-return paths are traced.
7. Generate an IPS patch from a hash-guarded manifest and test it in an emulator before calling it playable.

## Current status

- Read-only hook verifier is implemented and passes on the exact supplied ROM.
- Exact selector and dispatcher table offsets are recorded.
- The visible menu associated with the candidate selector is not yet runtime-confirmed.
- No ROM patch or game modification has been generated in this integration step.
