#!/usr/bin/env python3
"""Cross-repo qualification for AmiGuard quarantine -> route -> ASW import.

Uses the real amiguard-admin binary built from AmiGuard-Infrastructure and the
real ASW route importer. Fixtures are inert byte strings only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import asw_route_import  # noqa: E402

CASES = (
    ("amiga", "amiga", b"harmless-amiga-e2e-fixture\n"),
    ("atari-st", "atari", b"harmless-atari-st-e2e-fixture\n"),
    ("mac68k", "mac68k", b"harmless-mac68k-e2e-fixture\n"),
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_quarantine(root: Path, platform: str, submission_id: str, payload: bytes) -> str:
    namespace = root / platform
    namespace.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(namespace, 0o700)
    digest = hashlib.sha256(payload).hexdigest()
    (namespace / f"{submission_id}.sample").write_bytes(payload)
    os.chmod(namespace / f"{submission_id}.sample", 0o600)
    metadata = {
        "schema_version": 2,
        "kind": "amiguard-quarantine-submission",
        "submission_id": submission_id,
        "platform": platform,
        "sha256": digest,
        "size": len(payload),
        "received_at": now(),
        "consent": True,
        "executed": False,
        "extracted": False,
    }
    (namespace / f"{submission_id}.json").write_text(
        json.dumps(metadata, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.chmod(namespace / f"{submission_id}.json", 0o600)
    return digest


def run_admin(admin: Path, quarantine: Path, submission_id: str, inbox: Path) -> str:
    env = os.environ.copy()
    env["AMIGUARD_ADMIN_QUARANTINE_ROOT"] = str(quarantine)
    proc = subprocess.run(
        [str(admin), "route", submission_id, str(inbox)],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    return proc.stdout.strip()


def qualify(admin: Path) -> None:
    if not admin.is_file():
        raise SystemExit(f"admin binary not found: {admin}")

    with tempfile.TemporaryDirectory(prefix="asw-route-e2e-") as tmp:
        base = Path(tmp)
        quarantine = base / "quarantine"
        quarantine.mkdir(mode=0o700)
        inbox = base / "handoff"
        inbox.mkdir(mode=0o700)
        asw = base / "asw"
        asw.mkdir(mode=0o700)

        for _, namespace, _ in CASES:
            (inbox / namespace).mkdir(mode=0o700)
            (asw / namespace).mkdir(mode=0o700)

        for index, (platform, namespace, payload) in enumerate(CASES, 1):
            submission_id = f"{index:032x}"
            digest = write_quarantine(quarantine, platform, submission_id, payload)
            output = run_admin(admin, quarantine, submission_id, inbox)
            if "ROUTED" not in output or submission_id not in output:
                raise RuntimeError(f"unexpected route output: {output}")

            routed_sample = inbox / namespace / f"{submission_id}.sample"
            routed_manifest = inbox / namespace / f"{submission_id}.route.json"
            route = json.loads(routed_manifest.read_text(encoding="utf-8"))
            if route["platform"] != platform or route["asw_namespace"] != namespace:
                raise RuntimeError("routing manifest platform binding failed")
            if route["sha256"] != digest or route["size"] != len(payload):
                raise RuntimeError("routing manifest sample identity failed")

            ack = asw_route_import.import_route(asw, routed_sample, routed_manifest)
            if ack["result"] != "ACCEPTED" or ack["analysis_started"] is not False:
                raise RuntimeError("ASW acknowledgement contract failed")
            if ack["platform"] != platform or ack["asw_namespace"] != namespace:
                raise RuntimeError("ASW platform queue binding failed")
            if ack["sha256"] != digest:
                raise RuntimeError("ASW acknowledgement hash binding failed")

            queue_path = asw / namespace / "queue" / f"{submission_id}.json"
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
            if queue["status"] != "new" or queue["analysis_started"] is not False:
                raise RuntimeError("queue state must remain new and unexecuted")

            original = asw / namespace / "originals" / "sha256" / digest[:2] / f"{digest}.sample"
            if original.read_bytes() != payload:
                raise RuntimeError("immutable ASW original differs from quarantine fixture")
            if original.stat().st_mode & 0o777 != 0o400:
                raise RuntimeError("immutable ASW original is not read-only")

            print(f"PASS {platform} -> {namespace} submission={submission_id} sha256={digest}")

        # Cross-boundary tamper test: route a valid object, mutate the handoff,
        # then prove ASW rejects it before queue registration.
        submission_id = "f" * 32
        platform, namespace = "atari-st", "atari"
        write_quarantine(quarantine, platform, submission_id, b"harmless-tamper-source\n")
        run_admin(admin, quarantine, submission_id, inbox)
        routed_sample = inbox / namespace / f"{submission_id}.sample"
        routed_manifest = inbox / namespace / f"{submission_id}.route.json"
        routed_sample.write_bytes(b"tampered-after-routing\n")
        try:
            asw_route_import.import_route(asw, routed_sample, routed_manifest)
        except ValueError as exc:
            if "hash/size" not in str(exc):
                raise
        else:
            raise RuntimeError("ASW accepted a handoff modified after routing")
        if (asw / namespace / "queue" / f"{submission_id}.json").exists():
            raise RuntimeError("tampered handoff reached ASW queue")
        print("PASS tampered post-route handoff rejected before queue registration")

    print("M6.3/M7.11 CROSS-REPO HANDOFF QUALIFICATION: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admin", required=True, type=Path)
    args = parser.parse_args()
    qualify(args.admin.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
