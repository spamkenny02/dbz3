# Editor v7.1 packaging fix

The standalone ZIP places model.py at its root; the repository places it in
editor/. The campaign compiler previously assumed the repository layout and
failed with ModuleNotFoundError when launched from the standalone editor.
It now resolves the model from either layout relative to its own script.

Validation: 41 unit tests pass. The packaging regression test extracts the ZIP
into a directory containing spaces and accented characters, then runs the
compiler from a different working directory. A full build from that unpacked
ZIP using the exact original French ROM reproduced the v7 tested ROM and IPS
byte for byte. New Windows execution was not available here. The ROM patch is
unchanged; only editor packaging/import resolution is corrected.
