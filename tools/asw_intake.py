#!/usr/bin/env python3
"""Verified ASW sample intake. Never executes or extracts sample content."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from datetime import datetime, timezone

SHA_RE = re.compile(r"^[0-9a-f]{64}$")
SUBMISSION_RE = re.compile(r"^[0-9a-f]{32}$")
CHUNK = 1024 * 1024


def hash_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb", buffering=0) as f:
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            h.update(block)
            size += len(block)
    return h.hexdigest(), size


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def validate_source(path: Path) -> None:
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode):
        raise ValueError("source sample must not be a symlink")
    if not stat.S_ISREG(st.st_mode):
        raise ValueError("source sample must be a regular file")


def validate_args(expected_sha256: str, expected_size: int, submission_id: str, provenance: str) -> None:
    if not SHA_RE.fullmatch(expected_sha256):
        raise ValueError("expected SHA-256 must be 64 lowercase hex characters")
    if expected_size < 0:
        raise ValueError("expected size must be non-negative")
    if not SUBMISSION_RE.fullmatch(submission_id):
        raise ValueError("submission ID must be 32 lowercase hex characters")
    if not provenance or len(provenance) > 1024:
        raise ValueError("provenance must contain 1..1024 characters")


def secure_dirs(root: Path) -> tuple[Path, Path, Path]:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    originals = root / "originals" / "sha256"
    manifests = root / "manifests"
    tmp = root / "tmp"
    for d in (originals, manifests, tmp):
        d.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(d, 0o700)
    return originals, manifests, tmp


def verify_existing(path: Path, expected_sha256: str, expected_size: int) -> None:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("existing original is not a regular file")
    digest, size = hash_file(path)
    if digest != expected_sha256 or size != expected_size:
        raise RuntimeError("existing original does not match requested sample identity")


def import_sample(root: Path, sample: Path, submission_id: str, expected_sha256: str, expected_size: int, provenance: str) -> dict:
    validate_args(expected_sha256, expected_size, submission_id, provenance)
    validate_source(sample)
    digest, size = hash_file(sample)
    if digest != expected_sha256:
        raise ValueError("source SHA-256 does not match expected export metadata")
    if size != expected_size:
        raise ValueError("source size does not match expected export metadata")

    originals, manifests, tmp = secure_dirs(root)
    shard = originals / digest[:2]
    shard.mkdir(mode=0o700, exist_ok=True)
    os.chmod(shard, 0o700)
    final_sample = shard / f"{digest}.sample"
    final_manifest = manifests / f"{digest}.json"

    if final_sample.exists():
        verify_existing(final_sample, digest, size)
    else:
        fd, temp_name = tempfile.mkstemp(prefix="sample-", dir=tmp)
        temp_path = Path(temp_name)
        try:
            copied_hash = hashlib.sha256()
            copied_size = 0
            with os.fdopen(fd, "wb", buffering=0) as out, sample.open("rb", buffering=0) as src:
                while True:
                    block = src.read(CHUNK)
                    if not block:
                        break
                    out.write(block)
                    copied_hash.update(block)
                    copied_size += len(block)
                out.flush()
                os.fsync(out.fileno())
            if copied_hash.hexdigest() != digest or copied_size != size:
                raise RuntimeError("copied bytes failed verification")
            os.chmod(temp_path, 0o400)
            try:
                os.link(temp_path, final_sample)
            except FileExistsError:
                verify_existing(final_sample, digest, size)
            fsync_dir(shard)
        finally:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass

    manifest = {
        "schema_version": 1,
        "kind": "asw-sample-manifest",
        "asw_sample_id": digest,
        "sha256": digest,
        "size": size,
        "source_submission_id": submission_id,
        "imported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "provenance": provenance,
        "export_verified": True,
        "import_verified": True,
        "original_state": "sealed-read-only",
        "executed_on_host": False,
        "analysis_status": "new",
    }

    if not final_manifest.exists():
        fd, temp_name = tempfile.mkstemp(prefix="manifest-", dir=tmp, text=True)
        temp_manifest = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, sort_keys=True)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.chmod(temp_manifest, 0o600)
            try:
                os.link(temp_manifest, final_manifest)
            except FileExistsError:
                pass
            fsync_dir(manifests)
        finally:
            try:
                temp_manifest.unlink()
            except FileNotFoundError:
                pass

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="AmiGuard Signature Workstation verified intake")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="verify and import an exported sample")
    imp.add_argument("--root", required=True, type=Path)
    imp.add_argument("--sample", required=True, type=Path)
    imp.add_argument("--submission-id", required=True)
    imp.add_argument("--expected-sha256", required=True)
    imp.add_argument("--expected-size", required=True, type=int)
    imp.add_argument("--provenance", required=True)
    args = parser.parse_args()

    try:
        manifest = import_sample(
            args.root,
            args.sample,
            args.submission_id,
            args.expected_sha256,
            args.expected_size,
            args.provenance,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
