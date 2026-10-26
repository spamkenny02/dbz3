# Assembly integration status

No executable 65816 patch is included yet. The next source file should be added only after the user-facing menu and a safe WRAM allocation are confirmed. The intended architecture is to preserve the original global states, add a dedicated Story Mode state, route a new menu choice to it, and keep all story flags in volatile WRAM.

The current evidence is documented in docs/integration-next-steps.md. Do not treat the selector-limit bytes as a complete menu patch: the associated graphics/tilemap, confirmation routing, state tables, and runtime behavior must all be handled together.
