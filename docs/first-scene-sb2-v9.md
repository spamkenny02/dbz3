# V9 — one complete Gohan/Goten scene in the SB2 presentation

This release focuses on the first training scene. It keeps the original SB3
intro and HISTOIRE menu, and uses volatile WRAM only, with no SRAM.

## Windows workflow

1. Extract `Atelier_Premiere_Scene_SB2_v9.zip` into a new folder.
2. Copy your existing `assets/` folder beside `app.py` and install Pillow:
   `py -3 -m pip install -r requirements.txt`.
3. Launch `Lancer_editeur.bat`, then click **Créer la première scène SB2**.
4. Choose the original French **SB2 / La Légende Saien 2 MiB** ROM, then the
   original French **SB3 / Ultime Menace 2 MiB** ROM. The modified 4 MiB SB2
   Tools ROM is not the font/audio source for this operation.
5. Save the new project under a new JSON name. Preparation extracts private
   font/music resources into your asset directory and adds Goten from SB3.
   The asset catalog is backed up as `catalog.json.bak` before modification.
6. Select an SB2 music number, save, then choose **Construire ROM / IPS** with
   the original SB3 ROM and a separate output filename.
7. Start the resulting ROM in SNES9X from reset without an old save state.

The first scene has eight authoring nodes: forest, Gohan's appearance, both
brothers/dialogue, Goten's reply, fighter selection/combat, the two result
replies, and the end. Only one training fight is included. The editor can alter
the dialogue, layers and music. The route preview is a local simulation, not an
audio player or emulator. Music is heard when playing the built ROM.

## What is reproduced

The reference was checked in the original French SB2 and the supplied Tools
ROM. **Scene 13 is not a stretched full-screen forest:** it uses a central
forest band on a full 256x224 purple gradient composition, with actors in front
and dialogue below. V9 keeps that composition, without the v8 black title and
dialogue panels.

Gohan appears first, then Goten. These are successive fixed poses, not walking
or lip-sync animations. Gohan uses the existing SB2 cutscene asset. Goten is
extracted directly from a verified standing pose in the original SB3 ROM;
his pixels match the decoded native OBJ layer. Both supplied poses are Super
Saiyan. Goten is enlarged with nearest-neighbor sampling to suit the SB2 scene.
The fight still uses the native SB3 rocky-plain arena; it does not add a forest
combat stage.

The original French SB2 font is used, including lowercase and common French
accents. Dialogue starts at x=24/y=152 with 8x16 glyph cells and three lines.
Letters appear every three game frames. A first reveals the remainder of the
current page; a subsequent press advances. B exits the story and restores the
native title/audio flow. Both fighters can be selected. Victory and defeat
lead to different replies and rejoin the end of this scene.

## Font extraction and rendering

The native font resource starts at file offset `0x5231` in the exact French
SB2 image. Its LZ stream decompresses to 16,384 bytes. The extracted bytes were
compared with native VRAM `C000–FFFF` after scene initialization and match
exactly. Native BG3 uses 2bpp tiles with two 8x8 cells per glyph; the French
mapping includes lowercase E0–F9, uppercase 1D0–1E9, digits 1C0–1C9, accents
FA–107 and punctuation. The extraction/code is public; font pixels stay local.

SB3 uses the v8 Mode 3 compositor for this presentation. A shared tile set
contains the complete text and the pixels underneath it. Revealing a letter
updates two BG tilemap words during the frame handler, rather than re-uploading
the full bitmap per character. The covered background is preserved. The engine
rejects a progressive-text composition above 960 tiles or exhausted ROM/code
capacity. This reproduces the presentation; it is not a verbatim transplant of
the whole SB2 story interpreter.

## SB2 music and SB3 restoration

The selector currently uses source resource numbers **4–21**, without invented
song titles. Resource 4 is the default; resources 4 and 5 received complete
runtime checks. Other listed tracks have been extracted but have not each had
a full playthrough. The compiler embeds the selected sequence, the SB2 SPC
program and common samples from the user's original ROM.

SB2 and SB3 use different host audio protocols. Swapping their programs directly
would overwrite the currently executing IPL clone. The uploader first loads a
small SPC trampoline, patches the active clone's return, and transfers control
to the real SPC boot ROM. It then loads the selected game's program/data. All
handshake loops are bounded; `7E:1E66` records a failure.

While SB2 audio plays, the three native SB3 NMI audio services are gated only
when both the audio marker and Story state 12 are active. They are restored
before a native battle or B return. At the end of the fight, the story reloads
SB2 audio for its result dialogue. Tests compare the active program prefix
against the expected game driver and capture non-zero PCM in both music phases.
No sound file, ROM or extracted music is distributed in the public ZIP.

## Verification and scope

See `first-scene-sb2-v9-runtime.json` for results. The harness checks actor stages,
progressive text and its A behavior, exact completed-page RGB555 pixels, both
fighters, both outcomes, return to story, B return, and the restored SPC driver.
Four outcome runs manipulate health to reach the selected result (player health is reduced to one for a CPU finishing hit on loss); a further run allows the CPU to win without health changes.
A second music number is tested separately. The original menu modes, sampled
intro frames and the earlier three-battle campaign are checked for regression.

The updated GUI is tested under Linux/Tk/Xvfb, including preparation from the
original ROMs, native-font preview, music selection and a ROM matching the CLI.
The standalone ZIP is also prepared/built from a path with spaces and accents.
This new version has not itself been executed on Windows.

Original ROM hashes:

- SB2: `dd920a8f29dde8712a246a56d28ac0825d15c041d7f77f97dbeb37680751ce68`
- SB3: `663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa`

CLI:

```
python tools/prepare_first_scene.py sb2-original.sfc sb3-original.sfc editor/assets/catalog.json editor/premiere_scene_locale.json --track 4
python tools/build_story_campaign.py sb3-original.sfc editor/premiere_scene_locale.json --out-rom build/first.sfc --out-ips build/first.ips --report build/first.json
python tools/smoke_first_scene.py CORE.so build/first.sfc build/first.json --out build/first-smoke.json
```
