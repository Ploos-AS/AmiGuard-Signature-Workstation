#!/usr/bin/env python3
"""ASW -> AmiForensics downstream evidence/report adapter.

Consumes an ASW AmiSandbox runtime-evidence manifest, verifies the retained
artifacts, invokes AmiForensics' host-side report generator without a shell,
then verifies and hash-binds the resulting report. It never executes samples.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ASW_RUNTIME_KIND = "asw.amisandbox.runtime-evidence"
AMIFORENSICS_SCHEMA = "amiforensics.workstation.report/1"
MAX_REPORT_BYTES = 32 * 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_regular_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"expected regular non-symlink JSON file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_runtime_manifest(path: Path) -> tuple[dict, list[Path]]:
    data = load_regular_json(path)
    if data.get("kind") != ASW_RUNTIME_KIND:
        raise ValueError("unsupported ASW runtime manifest kind")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("runtime manifest has no artifacts")

    paths: list[Path] = []
    seen: set[str] = set()
    for item in artifacts:
        if not isinstance(item, dict):
            raise ValueError("invalid artifact entry")
        name = item.get("name")
        expected = item.get("sha256")
        raw_path = item.get("path")
        if not isinstance(name, str) or not isinstance(expected, str) or not isinstance(raw_path, str):
            raise ValueError("artifact entry missing name/path/sha256")
        if name in seen:
            raise ValueError(f"duplicate artifact: {name}")
        seen.add(name)
        p = Path(raw_path)
        st = p.lstat()
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            raise ValueError(f"artifact is not a regular non-symlink file: {name}")
        if p.name != name:
            raise ValueError(f"artifact path/name mismatch: {name}")
        actual = sha256_file(p)
        if actual.lower() != expected.lower():
            raise ValueError(f"artifact SHA-256 mismatch: {name}")
        paths.append(p)

    required = {"session.json", "events.jsonl"}
    if not required.issubset(seen):
        raise ValueError("runtime manifest lacks required AmiSandbox artifacts")
    return data, paths


def validate_report(report_path: Path, runtime_manifest: Path, artifacts: list[Path]) -> dict:
    st = report_path.lstat()
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise ValueError("AmiForensics report is not a regular non-symlink file")
    if st.st_size > MAX_REPORT_BYTES:
        raise ValueError("AmiForensics report exceeds size limit")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("schema") != AMIFORENSICS_SCHEMA:
        raise ValueError("unexpected AmiForensics report schema")

    manifest = report.get("manifest", {})
    if manifest.get("sha256") != sha256_file(runtime_manifest):
        raise ValueError("AmiForensics report manifest hash mismatch")

    expected = {p.name: sha256_file(p) for p in artifacts}
    observed: dict[str, str] = {}
    for item in report.get("evidence", []):
        if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("sha256"), str):
            observed[item["name"]] = item["sha256"]
    if observed != expected:
        raise ValueError("AmiForensics report evidence hashes do not match ASW runtime evidence")
    return report


def write_atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-manifest", required=True, type=Path)
    ap.add_argument("--amiforensics-report-tool", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--binding-manifest", required=True, type=Path)
    ap.add_argument("--amiforensics-revision", required=True)
    args = ap.parse_args()

    try:
        runtime, artifacts = validate_runtime_manifest(args.runtime_manifest)
        tool = args.amiforensics_report_tool.resolve(strict=True)
        if tool.is_symlink() or not tool.is_file():
            raise ValueError("AmiForensics report tool must be a regular non-symlink file")

        args.report.parent.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(tool), "--manifest", str(args.runtime_manifest)]
        for artifact in artifacts:
            cmd += ["--evidence", str(artifact)]
        cmd += ["--output", str(args.report)]
        completed = subprocess.run(cmd, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"AmiForensics report tool exited with status {completed.returncode}")

        validate_report(args.report, args.runtime_manifest, artifacts)
        binding = {
            "schema_version": 1,
            "kind": "asw.amiforensics.analysis",
            "sample": runtime.get("sample"),
            "runtime_manifest": {
                "path": str(args.runtime_manifest),
                "sha256": sha256_file(args.runtime_manifest),
            },
            "amiforensics": {
                "revision": args.amiforensics_revision,
                "report_schema": AMIFORENSICS_SCHEMA,
                "report": str(args.report),
                "report_sha256": sha256_file(args.report),
            },
        }
        write_atomic_json(args.binding_manifest, binding)
        print(json.dumps({"status": "PASS", "report": str(args.report), "binding_manifest": str(args.binding_manifest)}))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
