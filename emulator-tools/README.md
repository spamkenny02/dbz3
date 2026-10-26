# Diagnostic Snes9x core for SB2 extraction

The extractor uses normal libretro WRAM/VRAM access plus four read-only
snapshot pointers added by `snes9x-export.patch`:

- memory ID 42: 512 bytes of RGB555 CGRAM
- memory ID 43: 544 bytes of OAM
- memory ID 44: 32 KiB of register mirror / FillRAM
- memory ID 45: 64 KiB of SPC RAM, used to verify driver swaps and restoration

These IDs are a local diagnostic extension, not standard libretro IDs.
The GUI can edit the included catalog without any emulator installed.
A standard unmodified core suffices for SB3 smoke tests, but not extraction.

Reference build used here: upstream `snes9xgit/snes9x` commit
`1bcc369` (full revision available through the source checkout).
On Linux, with git, make and a C++ compiler:

```
git clone https://github.com/snes9xgit/snes9x.git
cd snes9x
git apply /path/to/dbz3/emulator-tools/snes9x-export.patch
make -C libretro -j4 LTO=
```

Select `libretro/snes9x_libretro.so` in the extractor. Windows users need a
matching-architecture Windows libretro DLL built with the same extension;
a Linux `.so` cannot be loaded by Windows Python. No core binary is bundled.
The in-memory SB2 probe sets boot state 5 and intercepts event initialization
at BF:8474. It uses an FF-checked 32-byte temporary code slot at FF:F000.
The user's original ROM is never changed or saved with these probes.
