#!/usr/bin/env python3
"""ASW Core CPU-agnostic evidence envelope validator."""

import argparse
import json
import re
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_PRODUCERS = {"runtime-backend", "forensic-interpreter", "static-analyzer", "core"}


def load_platforms(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {p["id"]: p for p in data["platforms"]}


def validate(doc: dict, platforms: dict[str, dict]) -> None:
    required = {"schema", "platform", "namespace", "sample", "producer", "evidence", "analysis_started"}
    if set(doc) != required:
        raise ValueError("evidence envelope field set mismatch")
    if doc["schema"] != "asw.core.evidence/1":
        raise ValueError("unsupported evidence schema")
    platform = platforms.get(doc["platform"])
    if platform is None:
        raise ValueError("unknown platform")
    if doc["namespace"] != platform["storage_namespace"]:
        raise ValueError("platform namespace mismatch")
    if doc["analysis_started"] is not False:
        raise ValueError("evidence envelope must not authorize analysis")

    sample = doc["sample"]
    if set(sample) != {"sha256", "size"} or not SHA256.fullmatch(sample["sha256"]):
        raise ValueError("invalid sample identity")
    if type(sample["size"]) is not int or sample["size"] < 0:
        raise ValueError("invalid sample size")

    producer = doc["producer"]
    if set(producer) != {"kind", "name", "revision"}:
        raise ValueError("invalid producer fields")
    if producer["kind"] not in ALLOWED_PRODUCERS:
        raise ValueError("invalid producer kind")
    if not isinstance(producer["name"], str) or not producer["name"]:
        raise ValueError("invalid producer name")
    if not isinstance(producer["revision"], str) or not producer["revision"]:
        raise ValueError("invalid producer revision")

    evidence = doc["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence list must not be empty")
    roles = set()
    for item in evidence:
        if set(item) != {"role", "sha256", "size"}:
            raise ValueError("invalid evidence item fields")
        if not isinstance(item["role"], str) or not item["role"] or item["role"] in roles:
            raise ValueError("invalid or duplicate evidence role")
        roles.add(item["role"])
        if not SHA256.fullmatch(item["sha256"]):
            raise ValueError("invalid evidence digest")
        if type(item["size"]) is not int or item["size"] < 0:
            raise ValueError("invalid evidence size")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("envelope", type=Path)
    parser.add_argument("--platforms", type=Path, default=Path("config/platforms.json"))
    args = parser.parse_args()
    doc = json.loads(args.envelope.read_text(encoding="utf-8"))
    validate(doc, load_platforms(args.platforms))
    print(f"VALID platform={doc['platform']} namespace={doc['namespace']} evidence={len(doc['evidence'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
