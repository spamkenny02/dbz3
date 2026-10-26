# Native Histoire v5 — restore the original introduction

V4 interpreted an ambiguous request as permission to bypass the intro.
V5 restores the original boot-state byte `$7F90=06`. Goku/Vegeta intro runs
normally. HISTOIRE remains first and selected in the following native menu.
B in the prologue returns to the original title flow, not the v4 direct-menu
startup. The unused direct initializer remains in source for now, unreachable
from boot; no title artwork is removed or replaced.

Validation: with no controller input, captures at frames 60, 120, 240 and 600
are byte-identical to captures from the original ROM using the same instrumented
Snes9x core. Snes9x 1.61 ran five 1,801-frame smoke scenarios: both prologue
routes and the three original menu entries. All passed, as did 25 unit tests.
The IPS reconstructs the tested ROM exactly. See `snes9x-v5-smoke-results.json`.
This does not claim a complete playthrough or a completed Story campaign.

Apply `patches/Ultime-Menace-Native-Histoire-v5.ips` to the original French
2 MiB ROM (SHA-256 `663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`),
not to v4. Open the resulting 4 MiB ROM under a new name, without loading an
old emulator save state. No SRAM or real Story battles are added.
