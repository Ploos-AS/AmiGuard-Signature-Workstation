#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import stat
import time
from pathlib import Path

TERMINAL_STATES = {"closed", "rejected"}
MARKER = ".asw-disposable-workspace.json"


def _regular_json(path: Path, what: str) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{what} must be a regular non-symlink file")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{what} root must be object")
    return obj


def _within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def inspect_workspace(data_root: Path, sample_id: str, min_age_days: int = 7, now_epoch=None) -> dict:
    if min_age_days < 0:
        raise ValueError("min_age_days must be non-negative")
    root = data_root.resolve()
    work_root = (root / "work").resolve()
    workspace = work_root / sample_id
    if workspace.is_symlink() or not workspace.is_dir():
        raise ValueError("workspace must be a real directory")
    resolved = workspace.resolve()
    if not _within(resolved, work_root) or resolved == work_root:
        raise ValueError("workspace escapes work root")

    marker = _regular_json(resolved / MARKER, "workspace marker")
    queue = _regular_json(root / "queue" / f"{sample_id}.json", "queue record")
    if marker.get("schema") != 1 or marker.get("sample_id") != sample_id:
        raise ValueError("workspace marker identity mismatch")
    sha = marker.get("sample_sha256")
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("invalid marker sample sha256")
    if queue.get("sample_id") != sample_id or queue.get("sample_sha256") != sha:
        raise ValueError("queue identity mismatch")
    state = queue.get("state")
    if state not in TERMINAL_STATES:
        return {"eligible": False, "reason": f"queue state is {state!r}, not terminal", "sample_id": sample_id, "sample_sha256": sha}

    for p in resolved.rglob("*"):
        if p.is_symlink():
            raise ValueError(f"workspace contains symlink: {p.relative_to(resolved)}")

    now_epoch = time.time() if now_epoch is None else now_epoch
    marker_mtime = (resolved / MARKER).stat().st_mtime
    age_seconds = max(0.0, now_epoch - marker_mtime)
    required = min_age_days * 86400
    if age_seconds < required:
        return {"eligible": False, "reason": "minimum retention age not reached", "sample_id": sample_id, "sample_sha256": sha, "age_days": age_seconds / 86400}
    return {"eligible": True, "reason": "terminal queue state and retention age satisfied", "sample_id": sample_id, "sample_sha256": sha, "age_days": age_seconds / 86400, "workspace": str(resolved)}


def purge_workspace(data_root: Path, sample_id: str, confirm_sha256: str, min_age_days: int = 7, now_epoch=None) -> dict:
    result = inspect_workspace(data_root, sample_id, min_age_days=min_age_days, now_epoch=now_epoch)
    if not result["eligible"]:
        raise ValueError(f"workspace not eligible: {result['reason']}")
    if confirm_sha256 != result["sample_sha256"]:
        raise ValueError("confirmation sha256 mismatch")
    workspace = Path(result["workspace"])
    shutil.rmtree(workspace)
    if workspace.exists():
        raise RuntimeError("workspace removal did not complete")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="ASW conservative retention/cleanup tool")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "purge"):
        s = sub.add_parser(name)
        s.add_argument("--root", type=Path, required=True, help="private ASW data root")
        s.add_argument("--sample-id", required=True)
        s.add_argument("--min-age-days", type=int, default=7)
        if name == "purge":
            s.add_argument("--confirm-sha256", required=True)
    args = p.parse_args()
    if args.cmd == "plan":
        result = inspect_workspace(args.root, args.sample_id, args.min_age_days)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["eligible"] else 2
    result = purge_workspace(args.root, args.sample_id, args.confirm_sha256, args.min_age_days)
    print(f"ASW cleanup: REMOVED {result['sample_id']} {result['sample_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
