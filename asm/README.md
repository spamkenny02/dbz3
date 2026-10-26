# Assembly integration status

The executable prototype is assembled by tools/build_story_prototype.py. It expands the ROM from 2 MiB to 4 MiB, stores new code/data in LoROM banks C0-FF, relocates the global state tables, and adds state 12 for branching Story Mode.

The normal title flow preserves the original selector. A hook before the original PPU/DMA upload writes HISTOIRE into the native menu's reserved fourth two-row slot using the game's original 16x16 glyph tiles. Selector limits change from 0-2 to 0-3, and the original final state-transition point routes index 3 to Story state 12. Story B returns to the original selector.

The custom four-choice menu code remains as an unused development fallback at state 13; the normal title/menu path does not enter it.

The patch is not emulator-tested and does not yet launch a real battle. See docs/menu-routing.md for patch offsets and docs/testing-prototype.md for the runtime checklist.
