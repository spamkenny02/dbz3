#!/usr/bin/env python3
"""Build an experimental, text-only branching Story Mode prototype for the exact
French Dragon Ball Z: Ultime Menace SNES ROM supplied by the user.

This tool never edits its input. It emits a separate ROM and IPS patch. The patch
has not been emulator-tested; use it as a development build, not a release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BASE_SHA256 = "663116d015cad3398644608ca6f2506071ab23d38b03b4890e1a6caecb1a55aa"
ROM_SIZE = 0x200000
BANK = 0xBE
PATCH_START = 0x1F1806
PATCH_END = 0x1F8000
INIT_TABLE_OFFSET = PATCH_START
FRAME_TABLE_OFFSET = PATCH_START + 14 * 3
CODE_ROM_START = PATCH_START + 14 * 3 * 2
CODE_CPU_START = 0x985A
FONT_OFFSET = 0x1F2000
FONT_CPU = 0xA000
MAP_OFFSETS = {
    "menu_0": 0x1F2400,
    "menu_1": 0x1F2C00,
    "menu_2": 0x1F3400,
    "menu_3": 0x1F3C00,
    "story_0": 0x1F4400,
    "story_1": 0x1F4C00,
    "choice_gohan": 0x1F5400,
    "choice_vegeta": 0x1F5C00,
    "ending_gohan": 0x1F6400,
    "ending_vegeta": 0x1F6C00,
}
MAP_CPU = {name: 0x8000 + (offset & 0x7FFF) for name, offset in MAP_OFFSETS.items()}
STORY_CURSOR = 0x7FFF50
STORY_PAGE = 0x7FFF51
STORY_ROUTE = 0x7FFF52

# Five-by-seven bitmap glyphs. Each row is left-to-right; this is original,
# minimal project UI art, not extracted game artwork.
FONT5X7: dict[str, tuple[str, ...]] = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ":": ("00000", "00100", "00100", "00000", "00100", "00100", "00000"),
    ";": ("00000", "00100", "00100", "00000", "00100", "00100", "01000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00110", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "11111", "00000", "11111", "00000", "00000", "00000"),
}


class Asm65816:
    """Tiny assembler for the small, fixed-opcode subset used by this prototype."""
    def __init__(self, origin: int):
        self.origin = origin
        self.pc = origin
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[str, int, str]] = []

    def emit(self, *values: int) -> None:
        self.code.extend(v & 0xFF for v in values)
        self.pc += len(values)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"Duplicate assembly label: {name}")
        self.labels[name] = self.pc

    def branch(self, opcode: int, label: str) -> None:
        self.emit(opcode, 0)
        self.fixups.append(("rel8", len(self.code) - 1, label))

    def jsl(self, label: str) -> None:
        self.emit(0x22, 0, 0, 0)
        self.fixups.append(("long", len(self.code) - 3, label))

    def finish(self) -> bytes:
        for kind, pos, label in self.fixups:
            if label not in self.labels:
                raise ValueError(f"Undefined assembly label: {label}")
            target = self.labels[label]
            if kind == "rel8":
                after_operand = self.origin + pos + 1
                delta = target - after_operand
                if not -128 <= delta <= 127:
                    raise ValueError(f"Branch to {label} is out of range: {delta} bytes")
                self.code[pos] = delta & 0xFF
            else:
                self.code[pos:pos + 3] = bytes((target & 0xFF, (target >> 8) & 0xFF, BANK))
        return bytes(self.code)


def lo_rom_cpu(offset: int) -> int:
    bank_index, in_bank = divmod(offset, 0x8000)
    if bank_index >= 0x80:
        raise ValueError("ROM offset cannot be represented by canonical LoROM mapping")
    return ((0x80 + bank_index) << 16) | (0x8000 + in_bank)


def pointer3(address: int) -> bytes:
    return bytes((address & 0xFF, (address >> 8) & 0xFF, (address >> 16) & 0xFF))


def make_font() -> bytes:
    result = bytearray()
    for code in range(32, 96):
        ch = chr(code)
        rows = FONT5X7.get(ch, ("00000",) * 7)
        plane0 = []
        for y in range(8):
            row = rows[y] if y < 7 else "00000"
            bits = 0
            for x, pixel in enumerate(row):
                if pixel == "1":
                    bits |= 1 << (6 - x)
            plane0.append(bits)
        result.extend(plane0)
        result.extend([0] * 8)
    if len(result) != 64 * 16:
        raise AssertionError("Font must contain 64 SNES 2bpp tiles")
    return bytes(result)


def make_map(lines: list[tuple[int, str, int, str]], cursor_row: int | None = None) -> bytes:
    """Create a 32x32 BG1 tilemap. Lines are (row, text, palette, alignment)."""
    words = [0] * (32 * 32)
    for row, text, palette, align in lines:
        text = text.upper()
        if align == "center":
            x = max(0, (32 - len(text)) // 2)
        elif align.startswith("left:"):
            x = int(align.split(":", 1)[1])
        else:
            x = 0
        for j, ch in enumerate(text[:max(0, 32 - x)]):
            code = ord(ch)
            tile = code - 32 if 32 <= code <= 95 else 0
            words[row * 32 + x + j] = tile | ((palette & 7) << 10)
    if cursor_row is not None:
        words[cursor_row * 32 + 4] = (ord(">") - 32) | (1 << 10)
    out = bytearray()
    for word in words:
        out.extend((word & 0xFF, (word >> 8) & 0xFF))
    if len(out) != 0x800:
        raise AssertionError("BG1 map must be 2048 bytes")
    return bytes(out)


def make_maps() -> dict[str, bytes]:
    option_rows = [10, 13, 16, 19]
    options = ["COMBAT SOLO", "COMBAT 2 JOUEURS", "TOURNOI", "HISTOIRE"]
    maps: dict[str, bytes] = {}
    for selected in range(4):
        lines = [
            (3, "ULTIME MENACE", 1, "center"),
            (6, "CHOISIS UN MODE", 0, "center"),
        ]
        for i, (row, label) in enumerate(zip(option_rows, options)):
            lines.append((row, f"{i + 1}  {label}", 1 if i == selected else 0, "left:7"))
        lines.extend([
            (24, "HAUT BAS : CHOISIR", 0, "center"),
            (26, "A : VALIDER  B : RETOUR", 1, "center"),
        ])
        maps[f"menu_{selected}"] = make_map(lines, cursor_row=option_rows[selected])

    maps["story_0"] = make_map([
        (3, "HISTOIRE - SAGA BUU", 1, "center"),
        (8, "LE TOURNOI DES ENFANTS", 0, "center"),
        (10, "SEMBLE ANODIN.", 0, "center"),
        (12, "MAIS UNE FORCE ANCIENNE", 0, "center"),
        (14, "SE PREPARE A REVEILLER", 0, "center"),
        (16, "MAJIN BOO.", 0, "center"),
        (24, "A : CONTINUER", 1, "center"),
        (26, "B : RETOUR MENU", 0, "center"),
    ])
    maps["story_1"] = make_map([
        (3, "UNE MENACE SE REVEILLE", 1, "center"),
        (8, "KAIOSHIN PREVIENT GOHAN :", 0, "center"),
        (10, "BABIDI CHERCHE A LIBERER", 0, "center"),
        (12, "MAJIN BOO.", 0, "center"),
        (14, "LE SORT DE LA TERRE", 0, "center"),
        (16, "DEPEND DE NOS CHOIX.", 0, "center"),
        (24, "A : CHOISIR LA ROUTE", 1, "center"),
        (26, "B : RETOUR MENU", 0, "center"),
    ])
    maps["choice_gohan"] = make_map([
        (3, "CHOIX DU HEROS", 1, "center"),
        (10, "AIDER GOHAN", 1, "center"),
        (15, "SUIVRE VEGETA", 0, "center"),
        (24, "HAUT BAS : CHOISIR", 0, "center"),
        (26, "A : VALIDER  B : MENU", 1, "center"),
    ], cursor_row=10)
    maps["choice_vegeta"] = make_map([
        (3, "CHOIX DU HEROS", 1, "center"),
        (10, "AIDER GOHAN", 0, "center"),
        (15, "SUIVRE VEGETA", 1, "center"),
        (24, "HAUT BAS : CHOISIR", 0, "center"),
        (26, "A : VALIDER  B : MENU", 1, "center"),
    ], cursor_row=15)
    maps["ending_gohan"] = make_map([
        (3, "ROUTE GOHAN", 1, "center"),
        (9, "TU REJOINS GOHAN", 0, "center"),
        (11, "POUR EMPECHER LE RITUEL.", 0, "center"),
        (13, "BABIDI N'A PAS DIT", 0, "center"),
        (15, "SON DERNIER MOT...", 0, "center"),
        (19, "FIN DU PROLOGUE A", 1, "center"),
        (24, "A : REJOUER", 1, "center"),
        (26, "B : MENU", 0, "center"),
    ])
    maps["ending_vegeta"] = make_map([
        (3, "ROUTE VEGETA", 1, "center"),
        (9, "VEGETA VEUT PROUVER", 0, "center"),
        (11, "SA FORCE A TOUT PRIX.", 0, "center"),
        (13, "LE COMBAT QUI S'ANNONCE", 0, "center"),
        (15, "VA TOUT CHANGER...", 0, "center"),
        (19, "FIN DU PROLOGUE B", 1, "center"),
        (24, "A : REJOUER", 1, "center"),
        (26, "B : MENU", 0, "center"),
    ])
    return maps


def assemble_code() -> tuple[bytes, dict[str, int]]:
    a = Asm65816(CODE_CPU_START)

    # State 12: narrative scene. Story state is volatile WRAM; no SRAM is used.
    a.label("StoryInit")
    a.emit(0x08, 0xE2, 0x20, 0xA9, 0x00, 0x8F, 0x51, 0xFF, 0x7F,
           0x8F, 0x52, 0xFF, 0x7F, 0x28, 0xC2, 0x10, 0xA2, 0x00, 0xC4)
    a.jsl("DrawScreen")
    a.emit(0x6B)

    a.label("StoryFrame")
    a.emit(0x8B, 0x08, 0xE2, 0x20, 0xA9, 0x00, 0x48, 0xAB, 0xC2, 0x30)
    a.emit(0xAD, 0x6D, 0x00, 0x29, 0x00, 0x80)
    a.branch(0xF0, "StoryCheckA")
    a.emit(0xE2, 0x20, 0xA9, 0x0D)
    a.emit(0x5C, 0x7A, 0x80, 0x80)
    a.label("StoryCheckA")
    a.emit(0xC2, 0x20, 0xAD, 0x6D, 0x00, 0x29, 0x80, 0x00)
    a.branch(0xF0, "StoryChoiceMove")
    a.emit(0xE2, 0x20, 0xAF, 0x51, 0xFF, 0x7F, 0xC9, 0x00)
    a.branch(0xF0, "StoryToPage1")
    a.emit(0xC9, 0x01)
    a.branch(0xF0, "StoryToChoice")
    a.emit(0xC9, 0x02)
    a.branch(0xF0, "StorySelectRoute")
    a.emit(0xA9, 0x00, 0x8F, 0x51, 0xFF, 0x7F, 0xC2, 0x10, 0xA2, 0x00, 0xC4)
    a.jsl("DrawScreen")
    a.emit(0x28, 0xAB, 0x6B)

    a.label("StoryToPage1")
    a.emit(0xA9, 0x01, 0x8F, 0x51, 0xFF, 0x7F, 0xC2, 0x10, 0xA2, 0x00, 0xCC)
    a.jsl("DrawScreen")
    a.emit(0x28, 0xAB, 0x6B)

    a.label("StoryToChoice")
    a.emit(0xA9, 0x02, 0x8F, 0x51, 0xFF, 0x7F, 0xA9, 0x00, 0x8F, 0x52, 0xFF, 0x7F)
    a.emit(0xC2, 0x10, 0xA2, 0x00, 0xD4)
    a.jsl("DrawScreen")
    a.emit(0x28, 0xAB, 0x6B)

    a.label("StorySelectRoute")
    a.emit(0xAF, 0x52, 0xFF, 0x7F)
    a.branch(0xF0, "StoryEndingGohan")
    a.emit(0xA9, 0x03, 0x8F, 0x51, 0xFF, 0x7F, 0xC2, 0x10, 0xA2, 0x00, 0xEC)
    a.jsl("DrawScreen")
    a.emit(0x28, 0xAB, 0x6B)
    a.label("StoryEndingGohan")
    a.emit(0xA9, 0x03, 0x8F, 0x51, 0xFF, 0x7F, 0xC2, 0x10, 0xA2, 0x00, 0xE4)
    a.jsl("DrawScreen")
    a.emit(0x28, 0xAB, 0x6B)

    a.label("StoryChoiceMove")
    a.emit(0xE2, 0x20, 0xAF, 0x51, 0xFF, 0x7F, 0xC9, 0x02)
    a.branch(0xD0, "StoryDone8")
    a.emit(0xC2, 0x20, 0xAD, 0x6D, 0x00, 0x29, 0x00, 0x08)
    a.branch(0xD0, "StoryToggleRoute")
    a.emit(0xAD, 0x6D, 0x00, 0x29, 0x00, 0x04)
    a.branch(0xF0, "StoryDone16")
    a.label("StoryToggleRoute")
    a.emit(0xE2, 0x20, 0xAF, 0x52, 0xFF, 0x7F, 0x49, 0x01, 0x8F, 0x52, 0xFF, 0x7F)
    a.branch(0xF0, "StoryDrawGohanChoice")
    a.emit(0xC2, 0x10, 0xA2, 0x00, 0xDC)
    a.jsl("DrawScreen")
    a.emit(0x28, 0xAB, 0x6B)
    a.label("StoryDrawGohanChoice")
    a.emit(0xC2, 0x10, 0xA2, 0x00, 0xD4)
    a.jsl("DrawScreen")
    a.emit(0x28, 0xAB, 0x6B)
    a.label("StoryDone16")
    a.emit(0x28, 0xAB, 0x6B)
    a.label("StoryDone8")
    a.emit(0x28, 0xAB, 0x6B)

    # State 13: four-choice menu. The first three options enter the original
    # mode-confirmation routine at BF:AAB7; option four enters state 12.
    a.label("MenuInit")
    a.emit(0x8B, 0x08, 0xE2, 0x20, 0xA9, 0x00, 0x48, 0xAB)
    # Run the complete original submode-2 initializer (including its common
    # tail) to prepare mode variables, then replace only its display.
    a.emit(0x22, 0x04, 0x81, 0xBF)
    a.emit(0xA9, 0x00, 0x8F, 0x50, 0xFF, 0x7F, 0x28, 0xAB, 0xC2, 0x10, 0xA2, 0x00, 0xA4)
    a.jsl("DrawScreen")
    a.emit(0x6B)

    a.label("MenuFrame")
    a.emit(0x8B, 0x08, 0xE2, 0x20, 0xA9, 0x00, 0x48, 0xAB, 0xC2, 0x30)
    a.emit(0xAD, 0x6D, 0x00, 0x29, 0x00, 0x08)
    a.branch(0xF0, "MenuCheckDown")
    a.emit(0xE2, 0x20, 0xAF, 0x50, 0xFF, 0x7F)
    a.branch(0xF0, "MenuUpWrap")
    a.emit(0x3A)
    a.branch(0x80, "MenuStoreCursor")
    a.label("MenuUpWrap")
    a.emit(0xA9, 0x03)
    a.label("MenuStoreCursor")
    a.emit(0x8F, 0x50, 0xFF, 0x7F)
    a.branch(0x80, "MenuRedraw")

    a.label("MenuCheckDown")
    a.emit(0xC2, 0x20, 0xAD, 0x6D, 0x00, 0x29, 0x00, 0x04)
    a.branch(0xF0, "MenuCheckA")
    a.emit(0xE2, 0x20, 0xAF, 0x50, 0xFF, 0x7F, 0xC9, 0x03)
    a.branch(0xF0, "MenuDownWrap")
    a.emit(0x1A)
    a.branch(0x80, "MenuStoreDown")
    a.label("MenuDownWrap")
    a.emit(0xA9, 0x00)
    a.label("MenuStoreDown")
    a.emit(0x8F, 0x50, 0xFF, 0x7F)
    a.branch(0x80, "MenuRedraw")

    a.label("MenuCheckA")
    a.emit(0xC2, 0x20, 0xAD, 0x6D, 0x00, 0x29, 0x80, 0x00)
    a.branch(0xF0, "MenuCheckB")
    a.emit(0xE2, 0x20, 0xAF, 0x50, 0xFF, 0x7F, 0xC9, 0x03)
    a.branch(0xF0, "MenuLaunchStory")
    a.emit(0x8D, 0x6C, 0x19, 0x9C, 0x6D, 0x19, 0x5C, 0xB7, 0xAA, 0xBF)
    a.label("MenuLaunchStory")
    a.emit(0x9C, 0x79, 0x18, 0xA9, 0x0C, 0x5C, 0x7A, 0x80, 0x80)

    a.label("MenuCheckB")
    a.emit(0xAD, 0x6D, 0x00, 0x29, 0x00, 0x80)
    a.branch(0xF0, "MenuDone")
    a.emit(0xE2, 0x20, 0x9C, 0x78, 0x18, 0x9C, 0x79, 0x18,
           0xA9, 0x06, 0x5C, 0x7A, 0x80, 0x80)

    a.label("MenuRedraw")
    a.emit(0xE2, 0x20, 0xAF, 0x50, 0xFF, 0x7F, 0xC9, 0x00)
    a.branch(0xF0, "MenuMap0")
    a.emit(0xC9, 0x01)
    a.branch(0xF0, "MenuMap1")
    a.emit(0xC9, 0x02)
    a.branch(0xF0, "MenuMap2")
    a.emit(0xC2, 0x10, 0xA2, 0x00, 0xBC)
    a.jsl("DrawScreen")
    a.branch(0x80, "MenuDone")
    a.label("MenuMap0")
    a.emit(0xC2, 0x10, 0xA2, 0x00, 0xA4)
    a.jsl("DrawScreen")
    a.branch(0x80, "MenuDone")
    a.label("MenuMap1")
    a.emit(0xC2, 0x10, 0xA2, 0x00, 0xAC)
    a.jsl("DrawScreen")
    a.branch(0x80, "MenuDone")
    a.label("MenuMap2")
    a.emit(0xC2, 0x10, 0xA2, 0x00, 0xB4)
    a.jsl("DrawScreen")
    a.label("MenuDone")
    a.emit(0x28, 0xAB, 0x6B)

    # Independent screen renderer: Mode 0, BG1 2bpp, 8x8 tiles, 32x32 map.
    a.label("DrawScreen")
    a.emit(0x8B, 0x08, 0xE2, 0x20, 0xC2, 0x10, 0xA9, 0x00, 0x48, 0xAB,
           0xAD, 0x43, 0x0B, 0x48, 0xDA, 0xA9, 0x00, 0x8D, 0x43, 0x0B, 0x8D, 0x00, 0x42,
           0xA9, 0x80, 0x8D, 0x00, 0x21,
           0xA9, 0x00, 0x8D, 0x05, 0x21, 0xA9, 0x40, 0x8D, 0x07, 0x21,
           0xA9, 0x00, 0x8D, 0x0B, 0x21, 0x8D, 0x0D, 0x21, 0x8D, 0x0D, 0x21,
           0x8D, 0x0E, 0x21, 0x8D, 0x0E, 0x21,
           0xA9, 0x01, 0x8D, 0x2C, 0x21,
           0xA9, 0x00, 0x8D, 0x2D, 0x21, 0x8D, 0x30, 0x21, 0x8D, 0x31, 0x21,
           0xA9, 0x00, 0x8D, 0x21, 0x21,
           0xA9, 0x00, 0x8D, 0x22, 0x21, 0x8D, 0x22, 0x21,
           0xA9, 0xFF, 0x8D, 0x22, 0x21, 0xA9, 0x7F, 0x8D, 0x22, 0x21,
           0xA9, 0x00, 0x8D, 0x22, 0x21, 0xA9, 0x7C, 0x8D, 0x22, 0x21,
           0xA9, 0xFF, 0x8D, 0x22, 0x21, 0xA9, 0x03, 0x8D, 0x22, 0x21,
           0xA9, 0x04, 0x8D, 0x21, 0x21,
           0xA9, 0x00, 0x8D, 0x22, 0x21, 0x8D, 0x22, 0x21,
           0xA9, 0xFF, 0x8D, 0x22, 0x21, 0xA9, 0x03, 0x8D, 0x22, 0x21,
           0xA9, 0xFF, 0x8D, 0x22, 0x21, 0xA9, 0x7F, 0x8D, 0x22, 0x21,
           0xA9, 0x00, 0x8D, 0x22, 0x21, 0xA9, 0x7C, 0x8D, 0x22, 0x21,
           0xA9, 0x80, 0x8D, 0x15, 0x21,
           0xA9, 0x00, 0x8D, 0x16, 0x21, 0x8D, 0x17, 0x21,
           0xA9, 0x01, 0x8D, 0x00, 0x43, 0xA9, 0x18, 0x8D, 0x01, 0x43,
           0xA9, 0x00, 0x8D, 0x02, 0x43, 0xA9, 0xA0, 0x8D, 0x03, 0x43,
           0xA9, 0xBE, 0x8D, 0x04, 0x43, 0xA9, 0x00, 0x8D, 0x05, 0x43,
           0xA9, 0x04, 0x8D, 0x06, 0x43, 0xA9, 0x01, 0x8D, 0x0B, 0x42,
           0xFA, 0xA9, 0x00, 0x8D, 0x16, 0x21, 0xA9, 0x20, 0x8D, 0x17, 0x21,
           0xA9, 0x01, 0x8D, 0x00, 0x43, 0xA9, 0x18, 0x8D, 0x01, 0x43,
           0x8E, 0x02, 0x43, 0xA9, 0xBE, 0x8D, 0x04, 0x43,
           0xA9, 0x00, 0x8D, 0x05, 0x43, 0xA9, 0x08, 0x8D, 0x06, 0x43,
           0xA9, 0x01, 0x8D, 0x0B, 0x42,
           0xA9, 0x0F, 0x8D, 0x00, 0x21,
           0x68, 0x8D, 0x43, 0x0B, 0x8D, 0x00, 0x42, 0x28, 0xAB, 0x6B)

    return a.finish(), a.labels


def make_ips(base: bytes, patched: bytes) -> bytes:
    out = bytearray(b"PATCH")
    i = 0
    while i < len(base):
        if base[i] == patched[i]:
            i += 1
            continue
        start = i
        while i < len(base) and base[i] != patched[i] and i - start < 0xFFFF:
            i += 1
        payload = patched[start:i]
        if start > 0xFFFFFF:
            raise ValueError("IPS offset exceeds 24-bit format")
        out.extend(start.to_bytes(3, "big"))
        out.extend(len(payload).to_bytes(2, "big"))
        out.extend(payload)
    out.extend(b"EOF")
    return bytes(out)


def read_ptrs(data: bytes, offset: int, count: int) -> list[int]:
    return [int.from_bytes(data[offset + 3*i:offset + 3*i + 3], "little") for i in range(count)]


def update_checksum(rom: bytearray) -> None:
    rom[0x7FDC:0x7FE0] = b"\x00\x00\x00\x00"
    checksum = (sum(rom) + 0x1FE) & 0xFFFF
    complement = checksum ^ 0xFFFF
    rom[0x7FDC:0x7FDE] = complement.to_bytes(2, "little")
    rom[0x7FDE:0x7FE0] = checksum.to_bytes(2, "little")


def build(base_path: Path, out_rom: Path, out_ips: Path, report_path: Path | None = None) -> dict:
    base = base_path.read_bytes()
    digest = hashlib.sha256(base).hexdigest()
    if len(base) != ROM_SIZE:
        raise ValueError(f"Expected a 2 MiB ROM, got {len(base)} bytes")
    if digest != BASE_SHA256:
        raise ValueError(f"Base ROM SHA-256 mismatch: expected {BASE_SHA256}, got {digest}")
    if base[PATCH_START:PATCH_END] != b"\xFF" * (PATCH_END - PATCH_START):
        raise ValueError("Candidate insertion area is not entirely FF on this ROM")

    # These three WRAM bytes have no direct long-address references in the base
    # ROM. Runtime memory traces are still required before treating them as proven free.
    for addr in (STORY_CURSOR, STORY_PAGE, STORY_ROUTE):
        needle = bytes((addr & 0xFF, (addr >> 8) & 0xFF, 0x7F))
        if needle in base:
            raise ValueError(f"Reserved WRAM byte {addr:06X} has an existing long-address reference")

    code, labels = assemble_code()
    if CODE_ROM_START + len(code) > FONT_OFFSET:
        raise ValueError(f"Code overlaps font data: end=0x{CODE_ROM_START + len(code):X}, font=0x{FONT_OFFSET:X}")

    # Preserve all 12 existing initializer pointers (state indices 0-11).
    init_ptrs = read_ptrs(base, 0x00F9, 12)
    frame_ptrs = read_ptrs(base, 0x02E3, 11)
    init_ptrs += [((BANK << 16) | labels["StoryInit"]), ((BANK << 16) | labels["MenuInit"])]
    frame_ptrs += [0x808304, ((BANK << 16) | labels["StoryFrame"]), ((BANK << 16) | labels["MenuFrame"])]
    if len(init_ptrs) != 14 or len(frame_ptrs) != 14:
        raise AssertionError("Expected global state indices 0..13")

    font = make_font()
    maps = make_maps()
    patched = bytearray(base)
    region = bytearray(b"\xFF" * (PATCH_END - PATCH_START))
    init_bytes = b"".join(pointer3(p) for p in init_ptrs)
    frame_bytes = b"".join(pointer3(p) for p in frame_ptrs)
    rel_init = INIT_TABLE_OFFSET - PATCH_START
    rel_frame = FRAME_TABLE_OFFSET - PATCH_START
    region[rel_init:rel_init + len(init_bytes)] = init_bytes
    region[rel_frame:rel_frame + len(frame_bytes)] = frame_bytes
    rel_code = CODE_ROM_START - PATCH_START
    region[rel_code:rel_code + len(code)] = code
    patched[PATCH_START:PATCH_END] = region

    patched[FONT_OFFSET:FONT_OFFSET + len(font)] = font
    for name, offset in MAP_OFFSETS.items():
        tilemap = maps[name]
        patched[offset:offset + len(tilemap)] = tilemap

    expected = {
        0x00E9: bytes.fromhex("F9 80 80"),
        0x00F1: bytes.fromhex("FB 80 80"),
        0x02D3: bytes.fromhex("E3 82 80"),
        0x02DB: bytes.fromhex("E5 82 80"),
        0x1F9A54: bytes.fromhex("A9 06"),
    }
    replacements = {
        0x00E9: bytes.fromhex("06 98 BE"),
        0x00F1: bytes.fromhex("08 98 BE"),
        0x02D3: bytes.fromhex("30 98 BE"),
        0x02DB: bytes.fromhex("32 98 BE"),
        0x1F9A54: bytes.fromhex("A9 0D"),
    }
    for offset, old in expected.items():
        if base[offset:offset + len(old)] != old:
            raise ValueError(f"Original hook mismatch at 0x{offset:X}: expected {old.hex()}, got {base[offset:offset+len(old)].hex()}")
        patched[offset:offset + len(old)] = replacements[offset]

    update_checksum(patched)
    if len(patched) != ROM_SIZE:
        raise AssertionError("Patched ROM size changed")
    if sum(patched) & 0xFFFF != int.from_bytes(patched[0x7FDE:0x7FE0], "little"):
        raise AssertionError("SNES checksum does not match byte sum")
    if (int.from_bytes(patched[0x7FDC:0x7FDE], "little") ^ int.from_bytes(patched[0x7FDE:0x7FE0], "little")) != 0xFFFF:
        raise AssertionError("SNES checksum complement is invalid")
    if read_ptrs(patched, INIT_TABLE_OFFSET, 14)[12] != ((BANK << 16) | labels["StoryInit"]):
        raise AssertionError("Story initializer pointer failed post-build verification")
    if read_ptrs(patched, FRAME_TABLE_OFFSET, 14)[12] != ((BANK << 16) | labels["StoryFrame"]):
        raise AssertionError("Story frame pointer failed post-build verification")
    if read_ptrs(patched, INIT_TABLE_OFFSET, 14)[13] != ((BANK << 16) | labels["MenuInit"]):
        raise AssertionError("Menu initializer pointer failed post-build verification")
    if read_ptrs(patched, FRAME_TABLE_OFFSET, 14)[13] != ((BANK << 16) | labels["MenuFrame"]):
        raise AssertionError("Menu frame pointer failed post-build verification")
    if patched[0x1F9A54:0x1F9A56] != bytes.fromhex("A9 0D"):
        raise AssertionError("Start hook failed post-build verification")

    ips = make_ips(base, bytes(patched))
    out_rom.parent.mkdir(parents=True, exist_ok=True)
    out_ips.parent.mkdir(parents=True, exist_ok=True)
    out_rom.write_bytes(patched)
    out_ips.write_bytes(ips)
    report = {
        "status": "experimental_static_build_not_emulator_tested",
        "base_file": base_path.name,
        "base_sha256": digest,
        "output_rom": str(out_rom),
        "output_rom_sha256": hashlib.sha256(patched).hexdigest(),
        "output_ips": str(out_ips),
        "output_ips_bytes": len(ips),
        "rom_bytes": len(patched),
        "code_bytes": len(code),
        "code_rom_start": f"0x{CODE_ROM_START:06X}",
        "code_rom_end_exclusive": f"0x{CODE_ROM_START + len(code):06X}",
        "labels": {name: f"{BANK:02X}:{addr:04X}" for name, addr in labels.items()},
        "init_table_offset": f"0x{INIT_TABLE_OFFSET:06X}",
        "frame_table_offset": f"0x{FRAME_TABLE_OFFSET:06X}",
        "reserved_wram": [f"0x{x:06X}" for x in (STORY_CURSOR, STORY_PAGE, STORY_ROUTE)],
        "menu_maps": {name: f"0x{offset:06X}" for name, offset in MAP_OFFSETS.items()},
        "checks": {
            "base_hash": True,
            "insertion_area_was_ff": True,
            "state_tables_relocated": True,
            "state_12_story": True,
            "state_13_menu": True,
            "start_hook": True,
            "checksum": True,
            "emulator_tested": False,
            "battle_hook_integrated": False,
        },
        "notes": [
            "The custom menu is a self-contained black-background text UI with a new 5x7 bitmap font.",
            "Menu options 0-2 seed the original selector variable and enter the original mode-confirmation routine; option 3 enters Story state 12.",
            "The first story slice has two intro pages, a two-way choice, and two distinct short endings.",
            "No SRAM is added; cursor/page/route flags are volatile WRAM only.",
            "This is not emulator-tested. Validate boot, DMA, controller input, mode routing and transitions in Mesen/bsnes before using it as a release patch.",
        ],
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="exact French Ultime Menace .sfc ROM")
    parser.add_argument("--out-rom", type=Path, default=Path("build/Ultime-Menace-Story-Prototype.sfc"))
    parser.add_argument("--out-ips", type=Path, default=Path("build/Ultime-Menace-Story-Prototype.ips"))
    parser.add_argument("--report", type=Path, default=Path("build/story-prototype-report.json"))
    args = parser.parse_args()
    report = build(args.rom, args.out_rom, args.out_ips, args.report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
