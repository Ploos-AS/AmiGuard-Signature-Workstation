#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required = [
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / ".gitignore",
    ROOT / "docs" / "M0_SAFETY_AND_TRUST_BOUNDARY.md",
]

for path in required:
    if not path.is_file():
        raise SystemExit(f"missing required file: {path.relative_to(ROOT)}")

for forbidden in ("samples", "quarantine", "intake", "work"):
    path = ROOT / forbidden
    if path.exists():
        raise SystemExit(f"forbidden repository path exists: {forbidden}")

bad_suffixes = {".sample", ".malware", ".infected", ".adf", ".hdf", ".img", ".iso"}
for path in ROOT.rglob("*"):
    if ".git" in path.parts or not path.is_file():
        continue
    if path.suffix.lower() in bad_suffixes:
        raise SystemExit(f"forbidden sample-like artifact: {path.relative_to(ROOT)}")

print("ASW repository safety checks: PASS")
