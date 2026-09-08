#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEXBYTES = re.compile(r"^(?:[0-9a-fA-F]{2})+$")
CANDIDATE_KINDS = {"file", "bootblock"}
SIGNATURE_TYPES = {"exact-sha256", "masked-pattern", "structural"}


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
        if not HEX64.fullmatch(digest) or digest != sample_sha:
            raise ValueError("exact signature hash must match sample_sha256")
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
        out_sig = None
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


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("candidate input must be a regular non-symlink file")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("candidate root must be object")
    return obj


def main() -> int:
    p = argparse.ArgumentParser(description="Validate/export ASW signature candidates")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("candidate", type=Path)
    e = sub.add_parser("export-amiguard")
    e.add_argument("candidate", type=Path)
    e.add_argument("--output", type=Path)
    args = p.parse_args()
    candidate = load(args.candidate)
    if args.cmd == "validate":
        validate_candidate(candidate)
        print("ASW candidate: VALID")
        return 0
    exported = export_amiguard(candidate)
    text = json.dumps(exported, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
