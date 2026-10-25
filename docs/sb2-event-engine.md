# La Légende Saien — event engine reference

**Purpose:** conceptual reference for the new Ultime Menace story mode. This is static analysis, not a claim that code can be copied between games at matching addresses.

## ROM identity

- Internal title: DRAGONBALL Z 2
- Size: 2,097,152 bytes
- SHA-256: dd920a8f29dde8712a246a56d28ac0825d15c041d7f77f97dbeb37680751ce68
- SRAM size byte: 00

## Global state 5 and scripts

- Global state table starts at 80:80E2; entry 5 points to BF:8474.
- Event setup helper around BF:8523 has special handling for event IDs 08-11, A0, C1, F5, and FC.
- Script pointer table begins at BF:B75B. Script index 1B00 selects a 16-bit pointer; the active indirect pointer uses direct page F0 with bank BF.
- The interpreter around BF:8067 reads a three-byte command into 1B02-1B04.
- Opcode family A0-B8 dispatches through a 25-entry table at BF:80AE.
- Opcode A0 at BF:80E0 copies 1B03 to 1B12, sets 1B21=1, and transitions to global state 5.
- A 256-entry scene-descriptor pointer table begins at BF:C35E, indexed by 1B12. The pointed data is binary scene configuration, not plain ASCII dialogue.

## Adaptation guidance

- Build a small, explicit story-script interpreter for Ultime Menace rather than transplanting Super Butoden 2 code verbatim.
- Reuse the idea of a compact command stream: show dialogue, set a volatile flag, branch on a choice or fight result, start a battle, and finish at one of several endings.
- Command encoding and the screen/resource format for the new game must be independently designed and tested.
- No SRAM is needed: reset story flags when starting a new run.

## Remaining unknowns

The full command semantics, scene-descriptor fields, dialogue encoding, and runtime transitions have not been completely decoded. A prototype should begin with one scene and one known battle transition, then be verified in an emulator.
