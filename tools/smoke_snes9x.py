#!/usr/bin/env python3
"""Run deterministic controller smoke checks using a supplied Snes9x libretro core.

Usage: python3 tools/smoke_snes9x.py CORE.so PATCHED.sfc SCENARIO
Scenarios: gohan, vegeta, combat, championnat, option. No ROM/core is bundled.
This checks game state and frame production; visual QA is still required.
"""
import ctypes as c
import hashlib
import json
import sys

core, rom, scenario = sys.argv[1:]
lib = c.CDLL(core)
frame = 0
screens = {}
actions = [(420, 3), (900, 8)]
if scenario in ('gohan', 'vegeta'):
    actions += [(1200, 8), (1300, 8), (1340, 8), (1420, 8), (1480, 0)]
    if scenario == 'vegeta':
        actions += [(1380, 5)]
else:
    index = ['combat', 'championnat', 'option'].index(scenario)
    actions += [(1050 + i * 40, 5) for i in range(index + 1)] + [(1200, 8)]

ENV = c.CFUNCTYPE(c.c_bool, c.c_uint, c.c_void_p)
VID = c.CFUNCTYPE(None, c.c_void_p, c.c_uint, c.c_uint, c.c_size_t)
AUD = c.CFUNCTYPE(None, c.c_int16, c.c_int16)
BATCH = c.CFUNCTYPE(c.c_size_t, c.c_void_p, c.c_size_t)
POLL = c.CFUNCTYPE(None)
INPUT = c.CFUNCTYPE(c.c_int16, c.c_uint, c.c_uint, c.c_uint, c.c_uint)

@ENV
def environment(command, data):
    if command == 10:  # SET_PIXEL_FORMAT: accept RGB565 only
        return c.cast(data, c.POINTER(c.c_int))[0] == 2
    return False

@VID
def video(data, width, height, pitch):
    if data and frame in (1040, 1160, 1260, 1320, 1360, 1450, 1800):
        screens[frame] = hashlib.sha256(c.string_at(data, pitch * height)).hexdigest()

@AUD
def audio(left, right):
    pass

@BATCH
def audio_batch(data, samples):
    return samples

@POLL
def poll():
    pass

@INPUT
def input_state(port, device, index, button):
    return int(port == 0 and device == 1 and
               any(button == key and start <= frame < start + 3 for start, key in actions))

for name, callback in [('environment', environment), ('video_refresh', video),
                       ('audio_sample', audio), ('audio_sample_batch', audio_batch),
                       ('input_poll', poll), ('input_state', input_state)]:
    getattr(lib, 'retro_set_' + name)(callback)
lib.retro_init()

class Game(c.Structure):
    _fields_ = [('path', c.c_char_p), ('data', c.c_void_p),
                ('size', c.c_size_t), ('meta', c.c_char_p)]

raw = open(rom, 'rb').read()
buffer = c.create_string_buffer(raw)
game = Game(None, c.cast(buffer, c.c_void_p), len(raw), None)
lib.retro_load_game.argtypes = [c.POINTER(Game)]
lib.retro_load_game.restype = c.c_bool
assert lib.retro_load_game(c.byref(game)), 'ROM load failed'
lib.retro_set_controller_port_device(0, 1)
lib.retro_set_controller_port_device(1, 1)
lib.retro_get_memory_data.argtypes = [c.c_uint]
lib.retro_get_memory_data.restype = c.c_void_p
ram = (c.c_ubyte * 131072).from_address(lib.retro_get_memory_data(2))
states = {}
early_menu_frames = []
for frame in range(1801):
    lib.retro_run()
    if 917 <= frame <= 932:
        vram = (c.c_ubyte * 65536).from_address(lib.retro_get_memory_data(3))
        tile = (vram[0xB490] | vram[0xB491] << 8) & 0x3FF
        assert tile == 0x302, f'HISTOIRE absent from first menu transfer at frame {frame}'
        early_menu_frames.append(frame)
    if frame in (1040, 1160, 1260, 1320, 1360, 1450, 1800):
        states[frame] = dict(global_state=ram[0x20], frame_state=ram[0x22],
                             screen=ram[0x23], main_cursor=ram[0x196B],
                             submenu=ram[0x25], page=ram[0x1FF51], route=ram[0x1FF52])
assert len(screens) == 7, 'Missing rendered frames'
assert states[1040]['global_state'] == 6 and states[1040]['screen'] == 12
assert states[1040]['main_cursor'] == 0  # HISTOIRE is the default after entering the menu
if scenario in ('gohan', 'vegeta'):
    assert states[1260]['global_state'] == states[1260]['frame_state'] == 12
    assert states[1320]['page'] == 1
    assert states[1360]['page'] == 2
    assert states[1450]['page'] == 3
    assert states[1450]['route'] == (scenario == 'vegeta')
    assert states[1800]['global_state'] == 6
    assert states[1800]['main_cursor'] == 0
    assert len({screens[i] for i in (1260, 1320, 1360, 1450)}) == 4
else:
    assert states[1360]['global_state'] == 6
    assert states[1360]['submenu'] == ['combat', 'championnat', 'option'].index(scenario) + 2
lib.retro_deinit()
print(json.dumps(dict(scenario=scenario, states=states, frame_sha256=screens, early_menu_frames=early_menu_frames), indent=2))
