# Testing the native-menu Story Mode patch

This is a development patch, not a release. Static checks and unit tests pass, but the ROM has not yet been run in an emulator.

## Before testing

1. Keep an untouched backup of your ROM.
2. Confirm the base image is the French Ultime Menace ROM with SHA-256 663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa.
3. Apply Ultime-Menace-Native-Histoire.ips to a copy using Floating IPS, Lunar IPS or another IPS patcher.
4. The patch expands the image from 2 MiB to 4 MiB. Use Mesen or bsnes with standard 4 MiB LoROM support.

## Expected result

- The original title screen and original menu artwork remain.
- The menu shows COMBAT, CHAMPIONNAT, OPTION and a fourth entry, HISTOIRE, underneath OPTION.
- Up/Down cycles through all four entries.
- Confirming COMBAT, CHAMPIONNAT or OPTION should follow the original code path.
- Confirming HISTOIRE should enter the Story Mode intro page.
- A advances through the two intro pages to the choice between AIDER GOHAN and SUIVRE VEGETA.
- The highlighted route should lead to a different short ending.
- A on an ending restarts the prologue; B returns to the original three-choice menu.
- Restarting the game should not preserve story route/page flags; no SRAM was added.

## If something fails

Please record the exact step that failed and attach a screenshot or short recording. Useful first checks in Mesen's debugger:

- Native menu label wrapper: C0:8337
- Story selection router: C0:846E
- Story return helper: C0:8483
- Original selector input handler: BF:AB48

A missing label may indicate the hook is too early/late relative to the map copy or PPU upload. A black screen or freeze may indicate a state-dispatch, LoROM mapping, DMA or register-setup issue. Do not overwrite the base ROM; the patch is disposable and can be rebuilt.

## Current limitations

- Native menu label visibility and input routing still need runtime testing.
- The menu uses original glyph tiles, but the story dialogue screen is still a text-only prototype.
- Story Mode does not launch a real battle yet.
