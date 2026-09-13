#!/usr/bin/env python3
"""ASW-owned validator/ingester for AtariSandbox M5 evidence."""

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_KINDS = {"screenshot", "memory_snapshot"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_child(root: Path, rel: str) -> Path:
    if not rel or Path(rel).is_absolute():
        raise ValueError("invalid evidence path")
    path = (root / rel).resolve()
    if root != path and root not in path.parents:
        raise ValueError("evidence path escapes source directory")
    return path


def validate_manifest(doc: dict) -> None:
    if doc.get("schema") != "atarisandbox.asw-ingest/1":
        raise ValueError("unsupported AtariSandbox ASW manifest schema")
    if doc.get("producer") != "AtariSandbox":
        raise ValueError("unexpected producer")
    if doc.get("network_enabled") is not False:
        raise ValueError("AtariSandbox networking must be disabled")
    if doc.get("host_shared_folders_enabled") is not False:
        raise ValueError("AtariSandbox host shared folders must be disabled")
    if not isinstance(doc.get("machine_profile"), str) or not doc["machine_profile"]:
        raise ValueError("missing machine profile")
    if not isinstance(doc.get("backend_revision"), str) or not doc["backend_revision"]:
        raise ValueError("missing backend revision")
    if not SHA256.fullmatch(doc.get("rom_sha256", "")):
        raise ValueError("invalid ROM SHA-256")
    if not SHA256.fullmatch(doc.get("source_manifest_sha256", "")):
        raise ValueError("invalid source-manifest SHA-256")
    objects = doc.get("objects")
    if not isinstance(objects, list) or not objects or len(objects) > 16:
        raise ValueError("invalid evidence object count")


def ingest(source: Path, destination: Path) -> dict:
    source = source.resolve()
    manifest_path = source / "asw-manifest.json"
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_manifest(doc)

    destination.mkdir(parents=True, exist_ok=True)
    retained = []
    seen = set()
    for item in doc["objects"]:
        if set(item) != {"kind", "path", "bytes", "sha256"}:
            raise ValueError("invalid evidence object fields")
        if item["kind"] not in ALLOWED_KINDS or item["kind"] in seen:
            raise ValueError("invalid or duplicate evidence kind")
        seen.add(item["kind"])
        if type(item["bytes"]) is not int or item["bytes"] <= 0 or item["bytes"] > 4 * 1024 * 1024:
            raise ValueError("invalid evidence object size")
        if not SHA256.fullmatch(item["sha256"]):
            raise ValueError("invalid evidence object SHA-256")
        src = safe_child(source, item["path"])
        if not src.is_file() or src.stat().st_size != item["bytes"] or sha256(src) != item["sha256"]:
            raise ValueError("evidence object identity mismatch")
        dst = destination / Path(item["path"]).name
        shutil.copyfile(src, dst)
        if sha256(dst) != item["sha256"]:
            raise ValueError("retained evidence hash mismatch")
        retained.append({"kind": item["kind"], "path": dst.name, "bytes": item["bytes"], "sha256": item["sha256"]})

    source_manifest = safe_child(source, doc["source_manifest"])
    if not source_manifest.is_file() or sha256(source_manifest) != doc["source_manifest_sha256"]:
        raise ValueError("source evidence manifest identity mismatch")

    result = {
        "schema": "asw.atarisandbox.ingestion/1",
        "platform": "atari-st",
        "namespace": "atari",
        "backend": "atarisandbox",
        "backend_revision": doc["backend_revision"],
        "machine_profile": doc["machine_profile"],
        "rom_sha256": doc["rom_sha256"],
        "network_enabled": False,
        "host_shared_folders_enabled": False,
        "source_asw_manifest_sha256": sha256(manifest_path),
        "source_evidence_manifest_sha256": doc["source_manifest_sha256"],
        "objects": retained,
        "result": "PASS",
    }
    out = destination / "asw-atarisandbox-ingestion.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    result = ingest(args.source, args.destination)
    print(f"PASS platform={result['platform']} objects={len(result['objects'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
