# Guarded IPS patch specification

The tools/make_ips.py utility creates an IPS file only if the ROM SHA-256 matches the specification and every expected byte sequence is present. Each replacement must be the same length as its original byte sequence; expansion and relocation are outside the current tool's scope.

Example format (illustrative only; not a real game patch):

```json
{
  "base_sha256": "SHA256_OF_YOUR_EXACT_BASE_ROM",
  "target_size": 2097152,
  "patches": [
    {
      "offset": "0x100",
      "expected_hex": "A9 00",
      "replacement_hex": "A9 01",
      "description": "Example two-byte change; do not use on the game"
    }
  ]
}
```

The example is intentionally not executable because the hash is a placeholder. For a real patch, record the exact original bytes, exact offset, rationale, and test status for every change. Never use guessed offsets or omit the hash guard.
