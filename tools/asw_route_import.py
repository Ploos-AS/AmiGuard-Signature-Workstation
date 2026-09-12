#!/usr/bin/env python3
"""Import a verified AmiGuard routing handoff into the correct ASW platform namespace."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from asw_intake import import_sample

ID_RE = re.compile(r"^[0-9a-f]{32}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
PLATFORM_TO_NAMESPACE = {"amiga": "amiga", "atari-st": "atari", "mac68k": "mac68k"}
MAX_MANIFEST = 64 << 10


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def require_regular(path: Path) -> None:
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise ValueError(f"{path} must be a regular non-symlink file")


def require_directory(path: Path) -> None:
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise ValueError(f"{path} must be an existing non-symlink directory")


def read_manifest(path: Path) -> dict:
    require_regular(path)
    if path.stat().st_size > MAX_MANIFEST:
        raise ValueError("routing manifest exceeds size limit")
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "schema_version", "kind", "submission_id", "platform", "asw_namespace",
        "sha256", "size", "received_at", "routed_at", "source",
    }
    if set(data) != expected:
        raise ValueError("routing manifest fields do not match contract")
    if data["schema_version"] != 1 or data["kind"] != "amiguard-asw-routing-manifest":
        raise ValueError("routing manifest contract mismatch")
    if not ID_RE.fullmatch(str(data["submission_id"])):
        raise ValueError("invalid submission id")
    if data["platform"] not in PLATFORM_TO_NAMESPACE:
        raise ValueError("unsupported platform")
    if PLATFORM_TO_NAMESPACE[data["platform"]] != data["asw_namespace"]:
        raise ValueError("platform/namespace mismatch")
    if not SHA_RE.fullmatch(str(data["sha256"])) or not isinstance(data["size"], int) or data["size"] < 0:
        raise ValueError("invalid sample identity")
    if data["source"] != "amiguard-public-quarantine":
        raise ValueError("unexpected routing source")
    return data


def hash_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb", buffering=0) as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    fd, temp_name = tempfile.mkstemp(prefix="ack-", dir=path.parent, text=True)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(temp, 0o600)
        os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def import_route(asw_root: Path, sample: Path, route_manifest: Path) -> dict:
    require_directory(asw_root)
    require_regular(sample)
    route = read_manifest(route_manifest)
    if sample.name != f"{route['submission_id']}.sample":
        raise ValueError("sample filename does not match routing submission id")
    if route_manifest.name != f"{route['submission_id']}.route.json":
        raise ValueError("routing manifest filename does not match submission id")
    digest, size = hash_file(sample)
    if digest != route["sha256"] or size != route["size"]:
        raise ValueError("routed sample hash/size verification failed")

    platform_root = asw_root / route["asw_namespace"]
    require_directory(platform_root)
    provenance = f"{route['source']}:{route['platform']}:{route['submission_id']}"
    manifest = import_sample(
        platform_root,
        sample,
        route["submission_id"],
        route["sha256"],
        route["size"],
        provenance,
    )

    queue_dir = platform_root / "queue"
    ack_dir = platform_root / "acks"
    queue_record = {
        "schema": "asw.platform.queue/1",
        "platform": route["platform"],
        "asw_namespace": route["asw_namespace"],
        "submission_id": route["submission_id"],
        "asw_sample_id": manifest["asw_sample_id"],
        "sha256": route["sha256"],
        "size": route["size"],
        "status": "new",
        "imported_at": manifest["imported_at"],
        "analysis_started": False,
    }
    atomic_json(queue_dir / f"{route['submission_id']}.json", queue_record)
    ack = {
        "schema": "asw.route.ack/1",
        "result": "ACCEPTED",
        "platform": route["platform"],
        "asw_namespace": route["asw_namespace"],
        "submission_id": route["submission_id"],
        "asw_sample_id": manifest["asw_sample_id"],
        "sha256": route["sha256"],
        "size": route["size"],
        "accepted_at": utcnow(),
        "route_manifest_verified": True,
        "sample_verified": True,
        "analysis_started": False,
    }
    atomic_json(ack_dir / f"{route['submission_id']}.json", ack)
    return ack


def main() -> int:
    p = argparse.ArgumentParser(description="ASW verified AmiGuard route importer")
    p.add_argument("--asw-root", required=True, type=Path)
    p.add_argument("--sample", required=True, type=Path)
    p.add_argument("--route-manifest", required=True, type=Path)
    args = p.parse_args()
    try:
        ack = import_route(args.asw_root, args.sample, args.route_manifest)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    print(json.dumps(ack, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
