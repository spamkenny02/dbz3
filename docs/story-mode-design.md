# Story mode design — no SRAM

## Requirements

- Add a branching story mode to the French release of Dragon Ball Z: Ultime Menace.
- Use the existing SNES battle engine where feasible.
- Keep all story state in volatile WRAM; do not add SRAM or persistent saves.
- Restarting the story resets flags so the player can pursue another route or ending.
- Keep the original ROM untouched and create a separate IPS/BPS patch only after hooks are verified.

## Minimal volatile state model

These are logical variables, not yet assigned to concrete WRAM addresses:

| Symbol | Purpose |
|---|---|
| story_active | Distinguishes story battles from normal play |
| chapter_id | Current scene/chapter |
| route_id | Selected narrative branch |
| choice_flags | Decisions already made in this run |
| last_fight_result | Win/loss/draw or game-defined result |
| ending_id | Ending to display |

At story start, clear all of these. A battle result advances the script or selects a branch. On an ending, return to the existing menu and clear story_active; a new story run begins from the initial scene.

## Prototype scope

The first playable slice should be deliberately small:

1. Add a fourth option to the existing mode selector.
2. Enter a story intro scene with two or three dialogue boxes.
3. Launch one existing battle using the game's own battle setup path.
4. Return to the story interpreter and branch based on the battle result.
5. Reach one of two short endings, both replayable by starting over.

No new character sprites or imported assets are required for this proof of concept; existing portraits/backgrounds can be reused if the relevant resources are understood.

## Integration plan (not yet implemented)

1. Trace the selector and confirm visible menu options from an emulator screenshot/debugger.
2. Confirm the state-6 confirmation path and cross-references to global state 5.
3. Identify unused WRAM; never infer that it is free solely because a variable appears unused in one code path.
4. Verify candidate ROM fill regions are unreferenced and safe for code/data.
5. Implement the smallest state-5 handler and test entry/exit before writing the script engine.
6. Trace battle entry and return, then connect one story battle.
7. Add branching and endings only after the prototype passes repeated emulator runs.

## Test checklist

- Normal menu options still work.
- Story option is selectable and cancel returns to the previous screen.
- Story variables reset on a fresh start and do not survive reset/power cycle.
- Win/loss paths both return to the script correctly.
- Both endings can be reached by replaying.
- No lockup during fade transitions or when holding buttons.
- Base ROM checksum/hash is validated before patch generation.
