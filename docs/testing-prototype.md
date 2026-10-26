# Testing the experimental Story Mode patch

This is a development patch, not a release. It has passed static checks and unit tests, but has **not** been run in a SNES emulator by the project build environment.

## Before testing

1. Keep an untouched backup of your ROM.
2. Confirm the base ROM is the French Ultime Menace image with SHA-256 `663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`.
3. Apply `Ultime-Menace-Story-Prototype.ips` to a copy using Floating IPS, Lunar IPS, or another IPS patcher.
4. Open the patched copy in Mesen or bsnes. Do not patch the La Légende Saien ROM.

## Expected prototype flow

- The original title screen appears.
- Press Start to enter the custom four-choice menu.
- Up/Down cycles through COMBAT SOLO, COMBAT 2 JOUEURS, TOURNOI, HISTOIRE.
- A on options 1-3 should invoke the original mode-confirmation/setup path.
- A on HISTOIRE should open the first story page.
- A advances to the second page, then to a choice between AIDER GOHAN and SUIVRE VEGETA.
- Up/Down toggles the highlighted route; A displays one of two short endings.
- A on an ending restarts the prologue; B returns to the custom menu.
- B on the custom menu returns to the original title screen.

## If it fails

Please note which step failed and include a screenshot or short recording. If using Mesen, a debugger trace/breakpoint at these new routines is useful:

- Story init: `BE:985A`
- Story frame handler: `BE:9872`
- Menu init: `BE:9956`
- Menu frame handler: `BE:9974`
- PPU/DMA renderer: `BE:9A34`

A black screen or freeze may indicate an issue with PPU register setup, DMA timing, state dispatch, or the original mode initializer. Do not overwrite the base ROM; the patch is disposable and can be rebuilt after corrections.

## Current limitations

- The menu is text-only and does not yet match Super Butoden 2's original presentation.
- The story currently has a narrative choice and two endings, but no real battle is launched yet.
- SRAM is not added; story flags are volatile WRAM only.
