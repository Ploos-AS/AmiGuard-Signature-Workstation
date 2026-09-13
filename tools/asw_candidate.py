#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEXBYTES = re.compile(r"^(?:[0-9a-fA-F]{2})+$")
CANDIDATE_KINDS = {"file", "bootblock"}
SIGNATURE_TYPES = {"exact-sha256", "masked-pattern", "structural"}
AAA_CONFIDENCE = {"single-engine", "corroborated", "confirmed"}
AAA_FAMILY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
CLAM_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def require(obj, key, typ):
    value = obj.get(key)
    if not isinstance(value, typ):
        raise ValueError(f"{key} must be {typ.__name__}")
    return value


def validate_candidate(candidate: dict) -> dict:
    if candidate.get("schema") != 1:
        raise ValueError("schema must be 1")
    cid = require(candidate, "id", str)
    if not cid or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,95}", cid):
        raise ValueError("invalid id")
    require(candidate, "name", str)
    require(candidate, "family", str)
    kind = require(candidate, "kind", str)
    if kind not in CANDIDATE_KINDS:
        raise ValueError("unsupported kind")
    if candidate.get("status") != "candidate":
        raise ValueError("status must be candidate")
    sample_sha = require(candidate, "sample_sha256", str).lower()
    if not HEX64.fullmatch(sample_sha):
        raise ValueError("sample_sha256 must be lowercase hex SHA-256")
    if "bootblock_sha256" in candidate:
        boot_sha = require(candidate, "bootblock_sha256", str).lower()
        if not HEX64.fullmatch(boot_sha):
            raise ValueError("bootblock_sha256 must be lowercase hex SHA-256")
    if "sample_size" in candidate:
        size = candidate["sample_size"]
        if not isinstance(size, int) or size < 0:
            raise ValueError("sample_size must be non-negative integer")
    if "created_at" in candidate and not isinstance(candidate["created_at"], str):
        raise ValueError("created_at must be RFC3339 string")
    if "aaa_confidence" in candidate and candidate["aaa_confidence"] not in AAA_CONFIDENCE:
        raise ValueError("invalid aaa_confidence")
    evidence = require(candidate, "evidence", dict)
    if evidence.get("sample_sha256") != sample_sha:
        raise ValueError("evidence sample_sha256 mismatch")
    if not isinstance(evidence.get("sources"), list) or not evidence["sources"]:
        raise ValueError("evidence.sources must be non-empty")
    signature = require(candidate, "signature", dict)
    stype = require(signature, "type", str)
    if stype not in SIGNATURE_TYPES:
        raise ValueError("unsupported signature type")
    if stype == "exact-sha256":
        digest = require(signature, "sha256", str).lower()
        if not HEX64.fullmatch(digest):
            raise ValueError("exact signature hash must be SHA-256")
        if kind == "file" and digest != sample_sha:
            raise ValueError("exact file signature hash must match sample_sha256")
        if kind == "bootblock":
            boot_sha = candidate.get("bootblock_sha256")
            if boot_sha is not None and digest != boot_sha:
                raise ValueError("exact bootblock signature hash must match bootblock_sha256")
    elif stype == "masked-pattern":
        pattern = require(signature, "pattern_hex", str)
        mask = require(signature, "mask_hex", str)
        if not HEXBYTES.fullmatch(pattern) or not HEXBYTES.fullmatch(mask):
            raise ValueError("pattern/mask must be even-length hex")
        if len(pattern) != len(mask):
            raise ValueError("pattern/mask length mismatch")
        if len(pattern) // 2 < 8:
            raise ValueError("masked pattern must be at least 8 bytes")
        offset = signature.get("offset")
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be non-negative integer")
    else:
        verifier = require(signature, "verifier", str)
        if not verifier or len(verifier) > 128:
            raise ValueError("invalid structural verifier")
    gates = require(candidate, "gates", dict)
    for gate in ("clean_corpus", "native_runtime", "manual_review"):
        if gates.get(gate) not in {"pending", "pass", "fail"}:
            raise ValueError(f"invalid gate state: {gate}")
    if gates.get("native_runtime") == "pass" and gates.get("clean_corpus") != "pass":
        raise ValueError("native runtime cannot pass before clean corpus")
    return candidate


def export_amiguard(candidate: dict) -> dict:
    validate_candidate(candidate)
    sig = candidate["signature"]
    out_sig = None
    verifier = candidate.get("verifier", "candidate-review-required")
    if sig["type"] == "exact-sha256":
        out_sig = {"type": "sha256", "value": sig["sha256"]}
    elif sig["type"] == "masked-pattern":
        out_sig = {
            "type": "masked-pattern",
            "offset": sig["offset"],
            "pattern_hex": sig["pattern_hex"].lower(),
            "mask_hex": sig["mask_hex"].lower(),
        }
    else:
        verifier = sig["verifier"]
    return {
        "schema": 1,
        "id": candidate["id"],
        "name": candidate["name"],
        "family": candidate["family"],
        "kind": candidate["kind"],
        "status": "research",
        "synthetic": False,
        "source": {
            "type": "asw-analysis",
            "note": "Generated from an ASW candidate; promotion requires AmiGuard qualification gates."
        },
        "provenance": {
            "derivation": candidate.get("derivation", "ASW analyst-derived candidate"),
            "redistribution_status": "sample-bytes-not-included"
        },
        "sample_sha256": candidate["sample_sha256"],
        "signature": out_sig,
        "verifier": verifier,
        "cleaner": "none",
        "research": {
            "asw_candidate": True,
            "evidence_sources": candidate["evidence"]["sources"],
            "clean_corpus_gate": candidate["gates"]["clean_corpus"],
            "native_runtime_gate": candidate["gates"]["native_runtime"],
            "manual_review_gate": candidate["gates"]["manual_review"],
            "promotion_gate": "Do not promote until all AmiGuard qualification gates pass."
        }
    }


def aaa_pattern_identity(pattern_hex: str, offset: int) -> str:
    identity = b"aaa-fixed-pattern-v1\x00" + f"offset:{offset}".encode() + b"\x00" + pattern_hex.lower().encode()
    return hashlib.sha256(identity).hexdigest()


def aaa_confidence(candidate: dict) -> str:
    explicit = candidate.get("aaa_confidence")
    if explicit:
        return explicit
    gates = candidate["gates"]
    if all(gates.get(g) == "pass" for g in ("clean_corpus", "native_runtime", "manual_review")):
        return "confirmed"
    return "single-engine"


def export_aaa(candidate: dict) -> dict:
    validate_candidate(candidate)
    family = candidate["family"]
    if not AAA_FAMILY.fullmatch(family):
        raise ValueError("AAA export requires family matching [A-Za-z0-9._-], max 64 chars")
    created_at = candidate.get("created_at")
    if not created_at:
        raise ValueError("AAA export requires candidate.created_at for deterministic provenance")
    sig = candidate["signature"]
    kind = None
    boot_sha = ""
    pattern = None
    identity_hash = candidate["sample_sha256"]
    if sig["type"] == "exact-sha256":
        if candidate["kind"] == "file":
            kind = "file-sha256"
        else:
            boot_sha = candidate.get("bootblock_sha256", "")
            if not boot_sha:
                raise ValueError("AAA bootblock export requires bootblock_sha256")
            kind = "bootblock-sha256"
            identity_hash = boot_sha
    elif sig["type"] == "masked-pattern":
        if sig["mask_hex"].lower() != "ff" * (len(sig["pattern_hex"]) // 2):
            raise ValueError("AAA native pattern candidate cannot represent masked bytes; require all-ff mask")
        kind = "pattern"
        pattern_hex = sig["pattern_hex"].lower()
        offset = sig["offset"]
        pattern = {"bytes_hex": pattern_hex, "offset": offset}
        identity_hash = aaa_pattern_identity(pattern_hex, offset)
    else:
        raise ValueError("AAA native candidate cannot represent structural verifier signatures")
    return {
        "schema": 1,
        "id": f"AAA.Amiga.{family}.{identity_hash[:16]}",
        "status": "candidate",
        "kind": kind,
        "malware_name": candidate["name"],
        "sample_sha256": candidate["sample_sha256"],
        **({"bootblock_sha256": boot_sha} if boot_sha else {}),
        **({"pattern": pattern} if pattern else {}),
        **({"sample_size": candidate["sample_size"]} if "sample_size" in candidate else {}),
        **({"format": candidate["format"]} if isinstance(candidate.get("format"), str) and candidate["format"] else {}),
        "source_engine": "AmiGuard-Signature-Workstation",
        "source_version": candidate.get("asw_version", "schema-1"),
        "detection_name": candidate["name"],
        "confidence": aaa_confidence(candidate),
        "created_at": created_at,
        "created_by": "aaa-signature-factory",
    }


def clamav_name(candidate: dict) -> str:
    raw = f"Amiga.{candidate['family']}.{candidate['id']}"
    name = CLAM_NAME.sub("_", raw).strip("._-")
    if not name:
        raise ValueError("cannot derive ClamAV signature name")
    return name[:128]


def clamav_hex(pattern_hex: str, mask_hex: str) -> str:
    pattern = bytes.fromhex(pattern_hex)
    mask = bytes.fromhex(mask_hex)
    out = []
    for p, m in zip(pattern, mask):
        if m == 0xFF:
            out.append(f"{p:02x}")
        elif m == 0x00:
            out.append("??")
        elif m == 0xF0:
            out.append(f"{p >> 4:x}?")
        elif m == 0x0F:
            out.append(f"?{p & 0x0f:x}")
        else:
            raise ValueError(f"ClamAV export cannot losslessly represent mask byte {m:02x}")
    return "".join(out)


def export_clamav(candidate: dict) -> tuple[str, str]:
    validate_candidate(candidate)
    sig = candidate["signature"]
    name = clamav_name(candidate)
    if sig["type"] == "exact-sha256":
        if candidate["kind"] != "file":
            raise ValueError("ClamAV hash signatures match complete files; bootblock hash requires a content signature")
        size = candidate.get("sample_size")
        if not isinstance(size, int) or size <= 0:
            raise ValueError("ClamAV SHA-256 export requires positive sample_size")
        return ".hsb", f"{sig['sha256'].lower()}:{size}:{name}"
    if sig["type"] == "masked-pattern":
        body = clamav_hex(sig["pattern_hex"], sig["mask_hex"])
        return ".ndb", f"{name}:0:{sig['offset']}:{body}"
    raise ValueError("ClamAV export does not support structural verifier signatures")


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("candidate input must be a regular non-symlink file")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("candidate root must be object")
    return obj


def write_or_print(text: str, output: Path | None) -> None:
    if output:
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main() -> int:
    p = argparse.ArgumentParser(description="Validate/export ASW signature candidates")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("candidate", type=Path)
    for name in ("export-amiguard", "export-aaa", "export-clamav"):
        e = sub.add_parser(name)
        e.add_argument("candidate", type=Path)
        e.add_argument("--output", type=Path)
    args = p.parse_args()
    candidate = load(args.candidate)
    if args.cmd == "validate":
        validate_candidate(candidate)
        print("ASW candidate: VALID")
        return 0
    if args.cmd == "export-amiguard":
        exported = export_amiguard(candidate)
        write_or_print(json.dumps(exported, indent=2, sort_keys=True) + "\n", args.output)
        return 0
    if args.cmd == "export-aaa":
        exported = export_aaa(candidate)
        write_or_print(json.dumps(exported, indent=2, sort_keys=True) + "\n", args.output)
        return 0
    extension, line = export_clamav(candidate)
    if args.output and args.output.suffix.lower() != extension:
        raise ValueError(f"ClamAV export requires {extension} output suffix")
    write_or_print(line + "\n", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
