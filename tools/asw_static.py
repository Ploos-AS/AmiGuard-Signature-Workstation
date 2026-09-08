#!/usr/bin/env python3
import argparse
import hashlib
import json
import struct
from pathlib import Path

HUNK_HEADER = 0x000003F3
MAX_STRINGS = 32
MAX_STRING_LEN = 96


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def amiga_boot_checksum_valid(block: bytes) -> bool | None:
    if len(block) < 1024:
        return None
    total = 0
    for (word,) in struct.iter_unpack(">I", block[:1024]):
        new = (total + word) & 0xFFFFFFFF
        if new < total:
            new = (new + 1) & 0xFFFFFFFF
        total = new
    return total == 0xFFFFFFFF


def bootblock_evidence(data: bytes) -> dict:
    if len(data) < 1024:
        return {"present": False, "reason": "input-shorter-than-1024-bytes"}
    block = data[:1024]
    marker = None
    if block[:3] == b"DOS":
        marker = {"family": "DOS", "flags": block[3]}
    words = [f"0x{x:08x}" for x in struct.unpack(">8I", block[:32])]
    return {
        "present": True,
        "sha256": sha256_bytes(block),
        "dos_marker": marker,
        "checksum_valid": amiga_boot_checksum_valid(block),
        "first_longwords": words,
    }


def hunk_evidence(data: bytes) -> dict:
    if len(data) < 4:
        return {"recognized": False, "reason": "input-shorter-than-4-bytes"}
    magic = struct.unpack_from(">I", data, 0)[0]
    if magic != HUNK_HEADER:
        return {"recognized": False, "magic": f"0x{magic:08x}"}

    out = {"recognized": True, "magic": "0x000003f3"}
    pos = 4
    resident_names = []
    try:
        while True:
            if pos + 4 > len(data):
                raise ValueError("truncated-resident-name-table")
            nlongs = struct.unpack_from(">I", data, pos)[0]
            pos += 4
            if nlongs == 0:
                break
            nbytes = nlongs * 4
            if nbytes > 4096 or pos + nbytes > len(data):
                raise ValueError("invalid-resident-name-length")
            raw = data[pos:pos+nbytes].rstrip(b"\0")
            resident_names.append(raw.decode("latin-1", errors="replace"))
            pos += nbytes
            if len(resident_names) >= 16:
                raise ValueError("too-many-resident-names")
        if pos + 12 > len(data):
            raise ValueError("truncated-hunk-table-header")
        table_size, first_hunk, last_hunk = struct.unpack_from(">III", data, pos)
        pos += 12
        if table_size > 4096 or last_hunk < first_hunk:
            raise ValueError("invalid-hunk-table-bounds")
        count = last_hunk - first_hunk + 1
        if count != table_size:
            raise ValueError("hunk-table-size-mismatch")
        if pos + count * 4 > len(data):
            raise ValueError("truncated-hunk-size-table")
        sizes = [struct.unpack_from(">I", data, pos + i * 4)[0] & 0x3FFFFFFF for i in range(count)]
        out.update({
            "resident_names": resident_names,
            "table_size": table_size,
            "first_hunk": first_hunk,
            "last_hunk": last_hunk,
            "hunk_sizes_longs": sizes[:128],
        })
    except ValueError as exc:
        out["parse_error"] = str(exc)
    return out


def printable_strings(data: bytes) -> list[str]:
    result = []
    current = bytearray()
    for b in data:
        if 32 <= b <= 126:
            current.append(b)
            if len(current) >= MAX_STRING_LEN:
                result.append(current.decode("ascii"))
                current.clear()
        else:
            if len(current) >= 4:
                result.append(current.decode("ascii"))
            current.clear()
        if len(result) >= MAX_STRINGS:
            break
    if len(result) < MAX_STRINGS and len(current) >= 4:
        result.append(current.decode("ascii"))
    return result[:MAX_STRINGS]


def classify(data: bytes) -> str:
    if len(data) >= 4 and struct.unpack_from(">I", data, 0)[0] == HUNK_HEADER:
        return "amiga-hunk"
    if len(data) >= 4 and data[:3] == b"DOS":
        return "amiga-dos-disk-or-bootblock"
    return "unknown"


def analyse(path: Path) -> dict:
    if path.is_symlink():
        raise ValueError("refusing symlink input")
    if not path.is_file():
        raise ValueError("input is not a regular file")
    data = path.read_bytes()
    return {
        "schema_version": 1,
        "sha256": sha256_bytes(data),
        "size": len(data),
        "kind": classify(data),
        "bootblock": bootblock_evidence(data),
        "hunk": hunk_evidence(data),
        "strings": printable_strings(data),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate host-safe ASW static evidence")
    parser.add_argument("sample", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = analyse(args.sample)
    text = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
