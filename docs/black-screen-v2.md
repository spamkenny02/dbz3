# Native Histoire v2 — menu stack correction

User report: Snes9x displays a black screen after the Goku/Vegeta introduction.
The original 7,414-byte IPS was reproduced byte for byte from the repository
and the supplied base ROM before changing the builder.

The NativeMenuAddStory hook saved A/X/Y before REP #$30, then restored them
as 16-bit registers. With an 8-bit caller this consumes extra stack bytes and
corrupts the return frame. REP now precedes the saves; PLP still restores the
caller's original widths after all registers have been restored.

The focused instruction test checks stack balance, A/X/Y, DBR and saved mode
bits in all four M/X combinations. It fails on the old code for three
combinations and passes on v2. All 24 unit tests pass. Applying the generated
IPS reproduces the generated 4 MiB ROM exactly.

This is a verified code defect and a plausible cause of the reported symptom;
it is not an emulator-confirmed diagnosis. No SNES emulator is installed in
the current environment. Boot, native menu rendering and Story transitions
remain unverified in Snes9x.

## Test in Snes9x

1. Apply `patches/Ultime-Menace-Native-Histoire-v2.ips` to a fresh, unmodified
   French ROM (2,097,152 bytes), not to a previously patched image.
2. Give the output a new filename and open it as a new ROM. Do not load a
   save state from the previous build.
3. Verify the introduction, original menu and four menu entries, then test
   entering HISTOIRE and returning with B.
4. Report the Snes9x version and the exact point of any remaining failure.

The prototype still contains no battles and is not a completed Story Mode.
