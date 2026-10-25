# Mode-selector hook — byte-level findings

**ROM:** French Ultime Menace, SHA-256
663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa

This note narrows the next implementation step to the existing three-position mode selector. The original ROM remains unchanged.

## Dispatch path

- Global state 6 initializer: CPU BF:8072, file offset 0x1F8072.
- State-6 frame-handler table: file offset 0x1F9ADF, 17 16-bit pointers within bank BF.
- Entry 12 points to BF:A96B.
- The nested dispatcher there uses variable 25. Its value 2 path enters BF:AA8F.
- BF:AA8F runs the fade path and calls the active input handler at BF:AB48 while the fade flag is clear.

## Exact selector limit instructions

The input handler updates cursor variable 196C.

| File offset | CPU address | Bytes | Meaning |
|---|---|---|---|
| 0x1FAB92 | BF:AB92 | A9 02 | When Up wraps from cursor 0, load cursor value 2 |
| 0x1FABB1 | BF:ABB1 | C9 02 | Down-path comparison against maximum cursor value 2 |

The first immediate and the second immediate are the obvious numerical limits for a fourth choice, but changing them alone is **not a complete or safe patch**. The drawing logic and the selected-mode setup paths must also support index 3.

## Confirmation path

After the selector fade completes, the current code copies 196C into 188C at file offset 0x1FAAF6 (bytes AD 6C 19 8D 8C 18). It later writes 05 to variable 1878 at file offset 0x1FAB18 (bytes A9 05 8D 78 18) and returns through the global transition gateway at 80:807A.

The subsequent setup code branches on 188C values 0, 1, and 2. A fourth option therefore needs an explicit branch before it can fall into any existing setup path.

## Next tasks before writing a ROM patch

1. Trace where the selector's menu tiles/tilemap and cursor-position data are loaded.
2. Find how each existing selection value 0, 1, and 2 maps to a visible label and a mode setup.
3. Add a fourth label and cursor position without overwriting other assets.
4. Route selected value 3 to the custom Story Mode state and initialize all volatile story flags.
5. Trace battle entry and return before connecting story events to fights.
6. Validate every patch hunk against exact original bytes and test the resulting ROM in an emulator.

## Safety notes

The candidate FF run at 0x1F1806–0x1F8000 is still only a candidate. The current tooling verifies the bytes are FF and the ROM hash matches; it does not prove that the range is unreferenced. No byte replacements or playable patch are included yet.
