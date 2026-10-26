# V7 — editor graph to native battles

This milestone compiles `editor/prelude_tournoi.json` into the existing native
HISTOIRE entry. Original Goku/Vegeta intro and menu fixes are retained.
No SRAM is added. Start a fresh game, not an older emulator state.

## What works

- 17 editable nodes: the brothers' training, Vegeta/Trunks training, Goku's
  return and the children's final, with different win/loss responses.
- Three genuine SB3 battles. Before each, choose either fighter; the other is
  CPU controlled. Both outcomes continue the narrative.
- Compiler for dialogue pages, up to three choices, automatic links, endings
  and combat events. Long dialogue is paginated; ASCII transliteration is
  required by the prototype bitmap font.
- GUI `Construire ROM / IPS` writes a separate ROM, IPS and build JSON from
  the loaded editor project. CLI equivalent:

```
python tools/build_story_campaign.py original.sfc editor/prelude_tournoi.json --out-rom build/prelude.sfc --out-ips build/prelude.ips --report build/prelude.json
```

The compiler checks the exact base hash, output-path separation, native hook
signature and bank capacity. Never apply the IPS to an already patched ROM.

## Integration and evidence

The tested native combat is global state **1**, initialized at `$87:DD17`.
The earlier state-4 hypothesis was insufficient. Player/CPU fighter IDs live
at `$0500`/`$0700`; health words at `$0562`/`$0762`. Human stays in slot zero,
including when the second fighter is selected. Native preparation uses
`$BF:CF87`; the transition wrapper at `$80:807A` only intercepts request 6
when a marked story battle is returning from state 1. It chooses the saved
win/loss destination and resumes Story state 12.

The battle initializer clears bank 7F, so old Story WRAM there cannot retain a
campaign. V7 uses `$7E:1E54–1E61`, below the native stack area. These bytes
survive the tested three-fight routes. This is runtime evidence for this
campaign, not proof for every possible future original-game mode or hook.
Code is in appended bank C1; narrative tilemaps start at C2. V6 remains intact
as its own source builder and patch.

Snes9x libretro upstream revision `1bcc369` was built for these tests. Four
full graph runs cover either selected character and either outcome of all
three battles. These runs inject zero health to exercise KO returns. A fifth
run uses **natural CPU victories** without health injection, through all
three battles and the final scene. B exits back to the native title flow.
The native COMBAT, CHAMPIONNAT and OPTION routing checks are also rerun.
See `campaign-v7-runtime.json`. Unit checks are in `tests/test_campaign.py`.

## Explicit visual limits

The ROM campaign currently uses **text screens**. SB2 backgrounds, layers,
Bulma/Chichi/Piccolo portraits and actor positioning are not encoded into the
SNES renderer. The editor keeps these compositions independently.
`staging` records the intended cast and location in the sample project; these
are authoring notes, not a claim of visible sprites. Assets must be assigned
from the user's local catalog. Goten and other Buu-era cutscene artwork may
need new assets beyond the extracted SB2 catalog.

The requested woods fight uses native terrain **6 (rocky plain)** for now.
It is explicitly named `plaine_rocheuse`; no forest is claimed. Terrain 5
is the gravity room; terrain 0 is the tournament. Native Gohan and Goten
fight with their original Super Saiyan sprites. New forms/forest terrain
and a graphical narrative renderer remain separate work.

The editor's `Tester depuis le début` simulates results locally; it does not
run an emulator. The ROM export launches real native battles when played.
Windows was confirmed by the user for the earlier editor. New Windows UI
and exporter require user testing; the compiler/runtime checks run on Linux.
