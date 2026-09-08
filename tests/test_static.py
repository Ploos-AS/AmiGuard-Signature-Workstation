import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("asw_static", ROOT / "tools" / "asw_static.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def make_valid_bootblock() -> bytes:
    words = [0x444F5300] + [0] * 255
    total = 0
    for word in words:
        new = (total + word) & 0xFFFFFFFF
        if new < total:
            new = (new + 1) & 0xFFFFFFFF
        total = new
    words[1] = (~total) & 0xFFFFFFFF
    data = b"".join(struct.pack(">I", w) for w in words)
    assert len(data) == 1024
    return data


def test_bootblock_checksum_and_marker():
    data = make_valid_bootblock()
    ev = mod.bootblock_evidence(data)
    assert ev["present"] is True
    assert ev["dos_marker"] == {"family": "DOS", "flags": 0}
    assert ev["checksum_valid"] is True
    assert ev["sha256"] == hashlib.sha256(data).hexdigest()


def test_short_input_is_bounded():
    assert mod.bootblock_evidence(b"abc") == {
        "present": False,
        "reason": "input-shorter-than-1024-bytes",
    }
    assert mod.hunk_evidence(b"abc")["recognized"] is False


def test_hunk_header_recognition():
    data = struct.pack(">IIIIIII", mod.HUNK_HEADER, 0, 1, 0, 0, 4, 0)
    ev = mod.hunk_evidence(data)
    assert ev["recognized"] is True
    assert ev["table_size"] == 1
    assert ev["first_hunk"] == 0
    assert ev["last_hunk"] == 0
    assert ev["hunk_sizes_longs"] == [4]


def test_analyse_deterministic_json(tmp_path):
    p = tmp_path / "fixture.bin"
    p.write_bytes(b"hello ASW\n")
    first = mod.analyse(p)
    second = mod.analyse(p)
    assert first == second
    encoded = json.dumps(first, indent=2, sort_keys=True) + "\n"
    assert encoded == json.dumps(second, indent=2, sort_keys=True) + "\n"
    assert first["kind"] == "unknown"
    assert first["strings"] == ["hello ASW"]


def test_symlink_refused(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"x")
    link = tmp_path / "link"
    link.symlink_to(target)
    try:
        mod.analyse(link)
    except ValueError as exc:
        assert str(exc) == "refusing symlink input"
    else:
        raise AssertionError("symlink input was accepted")
