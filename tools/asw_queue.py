#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

STATES = ("imported", "static-analysis", "runtime-analysis", "candidate", "qualification", "reviewed", "closed", "rejected")
TRANSITIONS = {
    "imported": {"static-analysis", "rejected"},
    "static-analysis": {"runtime-analysis", "candidate", "rejected"},
    "runtime-analysis": {"candidate", "rejected"},
    "candidate": {"qualification", "rejected"},
    "qualification": {"reviewed", "rejected"},
    "reviewed": {"closed", "qualification"},
    "closed": set(),
    "rejected": set(),
}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def now():
    return datetime.now(timezone.utc).isoformat()


def validate_record(r):
    if r.get("schema") != 1 or not ID_RE.fullmatch(r.get("sample_id", "")):
        raise ValueError("invalid queue record")
    if not SHA_RE.fullmatch(r.get("sample_sha256", "")):
        raise ValueError("invalid sample sha256")
    if r.get("state") not in STATES:
        raise ValueError("invalid state")
    history = r.get("history")
    if not isinstance(history, list) or not history:
        raise ValueError("history required")
    return r


def new_record(sample_id, sha256, note=None):
    if not ID_RE.fullmatch(sample_id) or not SHA_RE.fullmatch(sha256):
        raise ValueError("invalid sample id/hash")
    ts = now()
    event = {"at": ts, "from": None, "to": "imported"}
    if note: event["note"] = note
    return {"schema": 1, "sample_id": sample_id, "sample_sha256": sha256, "state": "imported", "created_at": ts, "updated_at": ts, "history": [event]}


def transition(r, target, note=None):
    validate_record(r)
    current = r["state"]
    if target not in TRANSITIONS[current]:
        raise ValueError(f"transition not allowed: {current} -> {target}")
    out = json.loads(json.dumps(r))
    ts = now()
    event = {"at": ts, "from": current, "to": target}
    if note: event["note"] = note
    out["state"] = target
    out["updated_at"] = ts
    out["history"].append(event)
    validate_record(out)
    return out


def atomic_write(path, obj, create=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if create else os.O_TRUNC)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True); f.write("\n")
        f.flush(); os.fsync(f.fileno())


def load(path):
    if path.is_symlink() or not path.is_file(): raise ValueError("queue record must be regular non-symlink file")
    return validate_record(json.loads(path.read_text(encoding="utf-8")))


def main():
    p = argparse.ArgumentParser(description="ASW analyst queue")
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("sample_id"); n.add_argument("sha256"); n.add_argument("--queue", type=Path, required=True); n.add_argument("--note")
    t = sub.add_parser("transition"); t.add_argument("record", type=Path); t.add_argument("target", choices=STATES); t.add_argument("--note")
    s = sub.add_parser("show"); s.add_argument("record", type=Path)
    a = p.parse_args()
    if a.cmd == "new":
        path = a.queue / f"{a.sample_id}.json"; atomic_write(path, new_record(a.sample_id, a.sha256, a.note), create=True); print(path)
    elif a.cmd == "transition":
        r = transition(load(a.record), a.target, a.note); atomic_write(a.record, r); print(r["state"])
    else:
        print(json.dumps(load(a.record), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
