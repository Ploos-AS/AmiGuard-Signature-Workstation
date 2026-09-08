#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

PROTECTED_TOPLEVEL = ("manifests", "queue", "audit", "evidence", "candidates")
OPTIONAL_ORIGINALS = "originals"
EXCLUDED = {"work", "tmp", "exports"}


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root, include_originals=False):
    roots = list(PROTECTED_TOPLEVEL)
    if include_originals:
        roots.append(OPTIONAL_ORIGINALS)
    for top in roots:
        base = root / top
        if not base.exists():
            continue
        if base.is_symlink() or not base.is_dir():
            raise ValueError(f"unsafe backup root: {top}")
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            d = Path(dirpath)
            for name in list(dirnames):
                p = d / name
                if p.is_symlink():
                    raise ValueError(f"symlink directory rejected: {p.relative_to(root)}")
            for name in filenames:
                p = d / name
                if p.is_symlink() or not p.is_file():
                    raise ValueError(f"non-regular file rejected: {p.relative_to(root)}")
                yield p


def build_manifest(root, include_originals=False):
    root = root.resolve()
    entries = []
    for p in sorted(iter_files(root, include_originals), key=lambda x: str(x.relative_to(root))):
        rel = p.relative_to(root).as_posix()
        top = rel.split("/", 1)[0]
        if top in EXCLUDED:
            raise ValueError("excluded path encountered")
        st = p.stat()
        entries.append({"path": rel, "size": st.st_size, "sha256": sha256_file(p)})
    return {
        "schema": 1,
        "kind": "asw-backup-manifest",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "include_originals": bool(include_originals),
        "files": entries,
    }


def verify_manifest(root, manifest):
    if manifest.get("schema") != 1 or manifest.get("kind") != "asw-backup-manifest":
        raise ValueError("invalid backup manifest")
    expected = {e["path"]: e for e in manifest.get("files", [])}
    actual_manifest = build_manifest(root, bool(manifest.get("include_originals")))
    actual = {e["path"]: e for e in actual_manifest["files"]}
    if set(expected) != set(actual):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise ValueError(f"file set mismatch missing={missing} extra={extra}")
    for path, exp in expected.items():
        got = actual[path]
        if exp.get("size") != got["size"] or exp.get("sha256") != got["sha256"]:
            raise ValueError(f"content mismatch: {path}")
    return {"files": len(actual)}


def load_manifest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("manifest must be regular non-symlink file")
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(path, manifest):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush(); os.fsync(f.fileno())


def main():
    p = argparse.ArgumentParser(description="ASW backup inventory and restore verifier")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create-manifest")
    c.add_argument("--root", type=Path, required=True)
    c.add_argument("--output", type=Path, required=True)
    c.add_argument("--include-originals", action="store_true")
    v = sub.add_parser("verify")
    v.add_argument("--root", type=Path, required=True)
    v.add_argument("--manifest", type=Path, required=True)
    a = p.parse_args()
    if a.cmd == "create-manifest":
        m = build_manifest(a.root, a.include_originals)
        write_manifest(a.output, m)
        print(f"ASW backup manifest: files={len(m['files'])} originals={m['include_originals']}")
        return 0
    r = verify_manifest(a.root, load_manifest(a.manifest))
    print(f"ASW restore verify: PASS files={r['files']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
