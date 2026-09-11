#!/usr/bin/env python3
"""ASW <-> AmiSandbox runner and evidence adapter.

The adapter deliberately does not fetch samples, ROMs or emulator binaries.
It launches a configured local AmiSandbox binary or ingests a completed
analysis directory, validates the minimum evidence contract, and writes an
ASW-owned runtime evidence manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILES = ROOT / "config" / "emulator-profiles.json"
MAX_ARTIFACT_BYTES = 128 * 1024 * 1024
REQUIRED_ARTIFACTS = ("session.json", "events.jsonl")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_profiles(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    backend = data.get("runtime_backend", {})
    if data.get("schema_version") != 2:
        raise ValueError("unsupported emulator profile schema")
    if backend.get("id") != "amisandbox" or backend.get("required") is not True:
        raise ValueError("AmiSandbox is not configured as the required runtime backend")
    return data


def select_profile(data: dict, profile_id: str) -> dict:
    matches = [p for p in data.get("profiles", []) if p.get("id") == profile_id]
    if len(matches) != 1:
        raise ValueError(f"unknown or ambiguous ASW profile: {profile_id}")
    p = matches[0]
    if not p.get("amisandbox_profile"):
        raise ValueError("profile lacks amisandbox_profile mapping")
    if p.get("jit") != "disabled":
        raise ValueError("ASW dynamic-analysis profile must disable JIT")
    if p.get("network_default") != "disabled":
        raise ValueError("ASW dynamic-analysis profile must disable networking by default")
    if p.get("shared_folders_default") != "disabled":
        raise ValueError("ASW dynamic-analysis profile must disable shared folders by default")
    return p


def validate_sample(sample: Path, expected_sha256: str | None) -> str:
    if not sample.is_file() or sample.is_symlink():
        raise ValueError("sample must be a regular non-symlink file")
    digest = sha256_file(sample)
    if expected_sha256 and digest.lower() != expected_sha256.lower():
        raise ValueError("sample SHA-256 mismatch")
    return digest


def validate_artifact(path: Path, root: Path) -> dict:
    resolved_root = root.resolve()
    resolved = path.resolve(strict=True)
    if resolved.parent != resolved_root:
        raise ValueError(f"artifact escaped analysis directory: {path.name}")
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise ValueError(f"artifact is not a regular non-symlink file: {path.name}")
    if st.st_size > MAX_ARTIFACT_BYTES:
        raise ValueError(f"artifact exceeds size limit: {path.name}")
    return {
        "name": path.name,
        "size": st.st_size,
        "sha256": sha256_file(path),
    }


def validate_evidence(analysis_dir: Path, expected_machine_profile: str) -> list[dict]:
    if not analysis_dir.is_dir() or analysis_dir.is_symlink():
        raise ValueError("analysis directory must be a real directory")
    artifacts = []
    for name in REQUIRED_ARTIFACTS:
        artifacts.append(validate_artifact(analysis_dir / name, analysis_dir))

    # Validate the stable session binding while treating events as opaque/versioned.
    session = json.loads((analysis_dir / "session.json").read_text(encoding="utf-8"))
    actual_profile = session.get("machine_profile")
    if actual_profile != expected_machine_profile:
        raise ValueError(
            "AmiSandbox machine profile mismatch: "
            f"expected {expected_machine_profile}, got {actual_profile!r}"
        )
    if session.get("jit_enabled") is not False:
        raise ValueError("AmiSandbox session evidence does not prove JIT disabled")

    with (analysis_dir / "events.jsonl").open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if line.strip():
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid events.jsonl line {line_no}: {exc}") from exc
    return artifacts


def copy_evidence(analysis_dir: Path, evidence_dir: Path, artifacts: list[dict]) -> list[dict]:
    evidence_dir.mkdir(parents=True, exist_ok=False)
    copied = []
    for meta in artifacts:
        src = analysis_dir / meta["name"]
        dst = evidence_dir / meta["name"]
        with src.open("rb") as rf, dst.open("xb") as wf:
            shutil.copyfileobj(rf, wf, length=1024 * 1024)
        digest = sha256_file(dst)
        if digest != meta["sha256"]:
            raise RuntimeError(f"evidence copy hash mismatch: {meta['name']}")
        copied.append({**meta, "path": str(dst)})
    return copied


def build_manifest(*, sample_id: str, sample_sha256: str, profile: dict,
                   amisandbox_revision: str, amisandbox_build: str,
                   started_at: int, ended_at: int, artifacts: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "kind": "asw.amisandbox.runtime-evidence",
        "sample": {"id": sample_id, "sha256": sample_sha256},
        "runtime": {
            "backend": "amisandbox",
            "revision": amisandbox_revision,
            "build": amisandbox_build,
            "asw_profile": profile["id"],
            "amisandbox_profile": profile["amisandbox_profile"],
            "jit": "disabled",
            "network": "disabled",
            "shared_folders": "disabled",
            "visible": bool(profile.get("visible", True)),
        },
        "started_at_unix": started_at,
        "ended_at_unix": ended_at,
        "artifacts": artifacts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True, type=Path)
    ap.add_argument("--sample-id", required=True)
    ap.add_argument("--sample-sha256")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    ap.add_argument("--analysis-dir", required=True, type=Path)
    ap.add_argument("--evidence-dir", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--amisandbox-revision", required=True)
    ap.add_argument("--amisandbox-build", required=True)
    ap.add_argument("--amisandbox-binary", type=Path)
    ap.add_argument("--config-fingerprint", default="asw-m6.7")
    ap.add_argument("--ingest-only", action="store_true")
    args, emulator_args = ap.parse_known_args()

    try:
        profiles = load_profiles(args.profiles)
        profile = select_profile(profiles, args.profile)
        sample_sha = validate_sample(args.sample, args.sample_sha256)

        started = int(time.time())
        if not args.ingest_only:
            if not args.amisandbox_binary:
                raise ValueError("--amisandbox-binary is required unless --ingest-only is used")
            binary = args.amisandbox_binary.resolve(strict=True)
            if not binary.is_file() or binary.is_symlink():
                raise ValueError("AmiSandbox binary must be a regular non-symlink file")
            args.analysis_dir.mkdir(parents=True, exist_ok=False)
            env = os.environ.copy()
            env.update({
                "AMISANDBOX_ANALYSIS_DIR": str(args.analysis_dir.resolve()),
                "AMISANDBOX_MACHINE_PROFILE": profile["amisandbox_profile"],
                "AMISANDBOX_CONFIG_FINGERPRINT": args.config_fingerprint,
            })
            # No shell=True: sample-controlled strings are never interpolated by a shell.
            cmd = [str(binary), *emulator_args]
            completed = subprocess.run(cmd, env=env, check=False)
            if completed.returncode != 0:
                raise RuntimeError(f"AmiSandbox exited with status {completed.returncode}")

        artifacts = validate_evidence(args.analysis_dir, profile["amisandbox_profile"])
        evidence_dir = args.evidence_dir / args.sample_id / f"amisandbox-{started}"
        copied = copy_evidence(args.analysis_dir, evidence_dir, artifacts)
        ended = int(time.time())
        manifest = build_manifest(
            sample_id=args.sample_id,
            sample_sha256=sample_sha,
            profile=profile,
            amisandbox_revision=args.amisandbox_revision,
            amisandbox_build=args.amisandbox_build,
            started_at=started,
            ended_at=ended,
            artifacts=copied,
        )
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=args.manifest.name + ".", dir=args.manifest.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, sort_keys=True)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, args.manifest)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        print(json.dumps({"status": "PASS", "manifest": str(args.manifest), "sample_sha256": sample_sha}))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
