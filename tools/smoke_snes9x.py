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
actions = []
if scenario in ('gohan', 'vegeta'):
    actions = [(300, 8), (400, 8), (440, 8), (520, 8), (580, 0)]
    if scenario == 'vegeta':
        actions += [(480, 5)]
else:
    index = ['combat', 'championnat', 'option'].index(scenario)
    actions = [(260 + i * 40, 5) for i in range(index + 1)] + [(400, 8)]

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
    if data and frame in (220, 280, 340, 420, 460, 550, 900):
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
for frame in range(901):
    lib.retro_run()
    if frame in (220, 280, 340, 420, 460, 550, 900):
        states[frame] = dict(global_state=ram[0x20], frame_state=ram[0x22],
                             screen=ram[0x23], main_cursor=ram[0x196B],
                             submenu=ram[0x25], page=ram[0x1FF51], route=ram[0x1FF52])
assert len(screens) == 7, 'Missing rendered frames'
assert states[220]['global_state'] == 6 and states[220]['screen'] == 12
assert states[220]['main_cursor'] == 0  # no controller input needed to reach menu
if scenario in ('gohan', 'vegeta'):
    assert states[340]['global_state'] == states[340]['frame_state'] == 12
    assert states[420]['page'] == 1
    assert states[460]['page'] == 2
    assert states[550]['page'] == 3
    assert states[550]['route'] == (scenario == 'vegeta')
    assert states[900]['global_state'] == 6 and states[900]['screen'] == 12
    assert states[900]['main_cursor'] == 0
    assert len({screens[i] for i in (340, 420, 460, 550)}) == 4
else:
    assert states[460]['global_state'] == 6
    assert states[460]['submenu'] == ['combat', 'championnat', 'option'].index(scenario) + 2
lib.retro_deinit()
print(json.dumps(dict(scenario=scenario, states=states, frame_sha256=screens), indent=2))
