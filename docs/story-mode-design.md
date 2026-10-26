# Story mode design — first playable-slice target

## Requirements

- Add a branching story experience to the French SNES release of Dragon Ball Z: Ultime Menace.
- Preserve the original three game modes.
- Keep all story state in volatile WRAM; do not add SRAM or persistent saves.
- Restarting the story resets flags so the player can pursue another route or ending.
- Keep the original ROM untouched and produce a separate hash-guarded IPS patch.

## Current prototype flow

1. From the title screen, Start enters a custom four-choice menu.
2. The first three options set the original selector variable and jump to the game's original mode-confirmation routine.
3. The fourth option enters a dedicated global state for the story.
4. The story displays two intro pages about the World Tournament and Babidi's plan.
5. The player chooses between helping Gohan and following Vegeta.
6. Each choice leads to a different short ending. A restarts the prologue; B returns to the custom menu.

The menu and story screens use a small original 5x7 font encoded as SNES 2bpp tiles. They render to BG1 in Mode 0, using a dedicated tilemap and palette. This avoids depending on unknown original font/tile IDs while the original screen assets are still being researched.

## State layout

- State 12: story initializer and per-frame handler.
- State 13: custom mode menu initializer and per-frame handler.
- Original state 11's special initializer remains intact.
- The relocated init/frame tables preserve original entries and append states 12-13.
- Variables: menu cursor `$7F:FF50`, story page `$7F:FF51`, route `$7F:FF52`.

These WRAM addresses are absent from direct long-address references in the base ROM, but a runtime memory trace is still required to prove they are safe.

## Next milestones

1. Test boot, menu navigation, cancel, and the three original mode routes in an emulator.
2. Verify the custom PPU setup/DMA code and adjust timing if necessary.
3. Find and reuse the original battle-entry and battle-return routines.
4. Replace the short ending-only branch with a story event that launches a real fight and branches on its result.
5. Add additional manga-inspired chapters and cutscenes, then test each path.

## Test checklist

- Original ROM hash matches before building.
- No SRAM header change.
- Title Start reaches state 13.
- Up/down cycles across all four options and highlights the current choice.
- Options 0-2 still enter their original game modes.
- Option 3 reaches state 12; A advances pages and selects a route; B returns to the menu.
- Both endings are reachable by replaying; no state persists across reset.
- No lockup during forced blank/DMA or state transitions.
