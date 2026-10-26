# Native Histoire v6 — no late HISTOIRE insertion

The menu's first fade DMA reads `$7E:8000` and uploads to VRAM `$59E0`.
The later per-frame highlighting uses `$7E:6000` and VRAM `$5A40`. V5 only
changed the latter, leaving the old three-row menu visible during the fade.

V6 hooks `$BF:A519`, after the original map copy and before the first fade
upload. It caches the three original rows in volatile `$7F:F800–F97F`, builds
the final four-entry map, and writes that map back into the first DMA source
at `$7E:80C0`. Subsequent palette/highlight updates use the cache, avoiding a
repeated shift. The cache is only meaningful while the title menu is active;
it is refreshed before every title-to-main-menu transition and is not SRAM.

## Runtime evidence

With Snes9x 1.61, using identical controller events, V5's VRAM first-slot
H-glyph position remains empty at frames 917–932, while the C of COMBAT is
present in the old first row. V6 has the H tile `$302` from frame 917, the
first populated menu transfer. All 16 early frames are asserted in each of
five smoke runs. Both prologue routes and original mode routing pass.
Returning from the COMBAT submenu was also checked for accidental repeated
row shifts. The original boot/intro route remains unchanged.

32 unit tests cover the ROM tools, graphics decoder, graph/project round-trip,
layer composition, probe guardrails and map context preservation. The final
IPS reproduces the exact ROM whose hash is in `snes9x-v6-smoke-results.json`.

Apply to the original French 2 MiB ROM, not V5. Output remains 4 MiB.
This patch fixes menu appearance; arbitrary scenes composed in the desktop
editor are not yet compiled into the SNES Story renderer.
