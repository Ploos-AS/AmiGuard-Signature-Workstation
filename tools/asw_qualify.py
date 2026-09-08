#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from asw_candidate import load, validate_candidate

GATES = ("clean_corpus", "native_runtime", "manual_review")


def load_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("evidence must be a regular non-symlink file")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("evidence root must be object")
    return obj


def apply_gate(candidate: dict, gate: str, evidence: dict) -> dict:
    validate_candidate(candidate)
    if gate not in GATES:
        raise ValueError("unsupported gate")
    if evidence.get("schema") != 1 or evidence.get("gate") != gate:
        raise ValueError("evidence schema/gate mismatch")
    if evidence.get("candidate_id") != candidate["id"]:
        raise ValueError("candidate id mismatch")
    if evidence.get("sample_sha256") != candidate["sample_sha256"]:
        raise ValueError("sample hash mismatch")
    result = evidence.get("result")
    if result not in {"pass", "fail"}:
        raise ValueError("evidence result must be pass or fail")
    if gate == "native_runtime" and candidate["gates"]["clean_corpus"] != "pass":
        raise ValueError("clean corpus must pass before native runtime")
    if gate == "manual_review" and candidate["gates"]["native_runtime"] != "pass":
        raise ValueError("native runtime must pass before manual review")
    if not isinstance(evidence.get("evidence"), list) or not evidence["evidence"]:
        raise ValueError("evidence list must be non-empty")
    updated = json.loads(json.dumps(candidate))
    updated["gates"][gate] = result
    q = updated.setdefault("qualification", {})
    q[gate] = evidence
    q["updated_at"] = datetime.now(timezone.utc).isoformat()
    validate_candidate(updated)
    return updated


def main() -> int:
    p = argparse.ArgumentParser(description="Apply evidence-backed ASW qualification gates")
    p.add_argument("candidate", type=Path)
    p.add_argument("--gate", choices=GATES, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    candidate = load(args.candidate)
    evidence = load_json(args.evidence)
    updated = apply_gate(candidate, args.gate, evidence)
    args.output.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"ASW qualification {args.gate}: {updated['gates'][args.gate].upper()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
