# Story Mode integration — next verified steps

## What the static trace now establishes

The fresh-boot flow starts in global state 6. The title/start handler at BF:9A3C (file offset 0x1F9A3C) checks the Start bit; the Start path writes `2` to `$1878` and clears `$1879` before returning through the state dispatcher. State-6 submode 2 resolves through the submode table to BF:8104 (file offset 0x1F8104), which calls the setup routine BF:874B (file offset 0x1F874B).

BF:874B loads the corresponding screen resources and initializes the state-6 substate machinery. The selector flow then reaches BF:AA8F (file offset 0x1FAA8F); when `$18A0 == 0`, this routine jumps directly to BF:AB48. That routine reads the controller, changes cursor variable `$196C), and uses the three-position bounds at 0x1FAB92 and 0x1FABB1. The confirmation path stores `$196C` to `$188C`, sets `$1878=5`, and returns through the state dispatcher.

This makes the BF:AB48 selector a strong static candidate for the first mode-selection screen after pressing Start. The menu's visible labels/tilemap still need to be identified before modifying the display.

## Verified exact-ROM facts

The supplied Ultime Menace ROM is 2 MiB, SHA-256 `663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`, internal title `DRAGONBALL Z3`, and SRAM-size byte 0.

| Purpose | File offset | Current bytes |
|---|---:|---|
| Start-to-submode-2 transition | `0x1F9A47` | `A9 02 8D 78 18 A9 00 8D 79 18` |
| Submode-2 setup entry | `0x1F8104` | `A9 0C 85 23 22 6D 82 BF 22 FA 85 BF 22 4B 87 BF` |
| Selector handler input path | `0x1FAA8F` | `E2 20 AD A0 18 D0 03 4C 48 AB` |
| Up-wrap limit in BF:AB48 | `0x1FAB92` | `A9 02` |
| Down limit in BF:AB48 | `0x1FABB1` | `C9 02` |
| Copy selector cursor to selected-mode variable | `0x1FAAF6` | `AD 6C 19 8D 8C 18` |
| Set state-6 submode 5 after selection | `0x1FAB18` | `A9 05 8D 78 18` |
| Return to state dispatcher | `0x1FAB32` | `5C 7A 80 80` |

The top-level global-state init table currently has 11 entries at file offset `0xF9`; the per-frame handler table has 11 entries at `0x2E3`. Each entry is a 24-bit long pointer, and the dispatcher indexes each table by `state * 3`.

## Candidate clean integration architecture

1. Decode the menu label/tilemap data loaded by BF:874B and determine where a fourth line can be drawn without overwriting existing assets.
2. Preserve the original 11 global states. If a dedicated state is needed, relocate both pointer tables into verified free ROM space, append a new state entry (candidate state 11), and patch both table-base operands in the dispatchers.
3. Extend the cursor wrap bounds only together with the label drawing and confirmation router. Existing choices must retain their current behavior; the new choice should set global state 11 and use the normal dispatcher.
4. Allocate volatile story flags only after WRAM usage is audited. No SRAM or persistent saves are planned.
5. Identify the existing text/portrait rendering path before implementing the first dialogue scene.
6. Connect a single existing battle only after the battle-entry and battle-return paths are traced.
7. Generate an IPS patch from a hash-guarded manifest and test it in an emulator before calling it playable.

## Current status

- Read-only hook verifier passes on the exact supplied ROM.
- Static control flow identifies the likely mode-selection path after Start.
- Menu label/tilemap resources and safe WRAM allocations remain unresolved.
- No ROM patch or game modification has been generated in this integration step.
