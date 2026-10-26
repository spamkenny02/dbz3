# Assembly integration status

The executable source for the current experimental prototype is assembled by `tools/build_story_prototype.py`. It relocates the global state tables, adds state 12 for the branching story and state 13 for a custom four-choice menu, and draws a self-contained text UI with SNES Mode 0 BG1 2bpp tiles.

The former selector-router-only approach is superseded: the new menu routes original options 0-2 to the existing mode-confirmation block at BF:AAB7, while option 3 enters state 12. The source builder is the current source of truth.

The prototype is not emulator-tested and does not yet launch a real battle. See `docs/integration-next-steps.md` for the current verification status.
