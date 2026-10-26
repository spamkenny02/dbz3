"""Small, deterministic Snes9x libretro host. No ROMs or save states bundled."""
import ctypes as C
import hashlib
from pathlib import Path

class Session:
    def __init__(self, core):
        self.lib = C.CDLL(str(Path(core).resolve()))
        self.frame = None
        self.buttons = set()
        self.disabled_layers = set()
        self.variables_changed = False
        self.pixel_format = 2
        self.callbacks = []
        self.strings = []
        class Variable(C.Structure):
            _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]
        def environment(command, data):
            if command == 10:
                value = C.cast(data, C.POINTER(C.c_int))[0]
                if value not in (0, 1, 2): return False
                self.pixel_format = value
                return True
            if command == 15:
                var = C.cast(data, C.POINTER(Variable)).contents
                key = var.key.decode()
                if key.startswith('snes9x_layer_'):
                    value = b'disabled' if int(key[-1]) in self.disabled_layers else b'enabled'
                    self.strings.append(value); var.value = value
                    return True
                return False
            if command == 17:
                C.cast(data, C.POINTER(C.c_bool))[0] = self.variables_changed
                self.variables_changed = False
                return True
            return False
        def video(data, w, h, pitch):
            if data: self.frame = (C.string_at(data, pitch*h), w, h, pitch, self.pixel_format)
        specs = [
            ('environment', C.CFUNCTYPE(C.c_bool,C.c_uint,C.c_void_p), environment),
            ('video_refresh', C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint,C.c_size_t), video),
            ('audio_sample', C.CFUNCTYPE(None,C.c_int16,C.c_int16), lambda a,b:None),
            ('audio_sample_batch', C.CFUNCTYPE(C.c_size_t,C.c_void_p,C.c_size_t), lambda a,n:n),
            ('input_poll', C.CFUNCTYPE(None), lambda:None),
            ('input_state', C.CFUNCTYPE(C.c_int16,C.c_uint,C.c_uint,C.c_uint,C.c_uint),
             lambda p,d,i,b:int(p==0 and d==1 and b in self.buttons))]
        for name, typ, func in specs:
            cb=typ(func); self.callbacks.append(cb)
            getattr(self.lib,'retro_set_'+name)(cb)
        self.lib.retro_init()
        self.lib.retro_get_memory_data.argtypes=[C.c_uint]
        self.lib.retro_get_memory_data.restype=C.c_void_p
        self.loaded=False

    def load(self, data):
        if self.loaded: self.lib.retro_unload_game()
        class Game(C.Structure):
            _fields_=[('path',C.c_char_p),('data',C.c_void_p),('size',C.c_size_t),('meta',C.c_char_p)]
        self.rom_buffer=C.create_string_buffer(data)
        game=Game(None,C.cast(self.rom_buffer,C.c_void_p),len(data),None)
        self.lib.retro_load_game.argtypes=[C.POINTER(Game)]
        self.lib.retro_load_game.restype=C.c_bool
        if not self.lib.retro_load_game(C.byref(game)): raise RuntimeError('Snes9x refused ROM')
        self.loaded=True
        self.lib.retro_set_controller_port_device(0,1)
        self.lib.retro_set_controller_port_device(1,1)
        self.frame=None; self.buttons=set()

    def run(self, frames=1):
        for _ in range(frames): self.lib.retro_run()

    def memory(self, kind, size):
        ptr=self.lib.retro_get_memory_data(kind)
        if not ptr: raise RuntimeError(f'Core lacks memory export {kind}; use the diagnostic core patch')
        return C.string_at(ptr,size)

    def layers(self, disabled):
        self.disabled_layers=set(disabled); self.variables_changed=True

    def image(self):
        from PIL import Image
        if not self.frame: raise RuntimeError('No rendered frame')
        raw,w,h,pitch,fmt=self.frame
        out=bytearray(w*h*3)
        for y in range(h):
            for x in range(w):
                n=int.from_bytes(raw[y*pitch+x*(4 if fmt==1 else 2):y*pitch+x*(4 if fmt==1 else 2)+(4 if fmt==1 else 2)],'little')
                if fmt==2: rgb=((n>>11&31)*255//31,(n>>5&63)*255//63,(n&31)*255//31)
                elif fmt==0: rgb=((n>>10&31)*255//31,(n>>5&31)*255//31,(n&31)*255//31)
                else: rgb=(n>>16&255,n>>8&255,n&255)
                at=(y*w+x)*3;out[at:at+3]=bytes(rgb)
        return Image.frombytes('RGB',(w,h),bytes(out))

    def close(self):
        if self.loaded: self.lib.retro_unload_game()
        self.lib.retro_deinit()
