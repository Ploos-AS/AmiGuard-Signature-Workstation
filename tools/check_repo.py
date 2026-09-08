#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

required = [
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / ".gitignore",
    ROOT / "docs" / "M0_SAFETY_AND_TRUST_BOUNDARY.md",
    ROOT / "docs" / "M1_VERIFIED_INTAKE.md",
    ROOT / "docs" / "M1_REFERENCE_ANTIVIRUS_SUITE.md",
    ROOT / "schemas" / "sample-manifest.schema.json",
    ROOT / "reference-antivirus" / "catalog.json",
    ROOT / "tools" / "asw_intake.py",
]

for path in required:
    if not path.is_file():
        raise SystemExit(f"missing required file: {path.relative_to(ROOT)}")

for forbidden in ("samples", "quarantine", "intake", "work"):
    path = ROOT / forbidden
    if path.exists():
        raise SystemExit(f"forbidden repository path exists: {forbidden}")

bad_suffixes = {".sample", ".malware", ".infected", ".adf", ".hdf", ".img", ".iso", ".lha", ".lzh", ".7z", ".rar"}
for path in ROOT.rglob("*"):
    if ".git" in path.parts or not path.is_file():
        continue
    if path.suffix.lower() in bad_suffixes:
        raise SystemExit(f"forbidden sample-like artifact: {path.relative_to(ROOT)}")

catalog = json.loads((ROOT / "reference-antivirus" / "catalog.json").read_text())
if catalog.get("policy") != "metadata-only-no-binaries":
    raise SystemExit("reference antivirus catalog must remain metadata-only")
if len(catalog.get("tools", [])) < 6:
    raise SystemExit("reference antivirus catalog unexpectedly incomplete")
for tool in catalog["tools"]:
    if tool.get("binary_sha256") is not None or tool.get("provenance") is not None:
        raise SystemExit("public catalog must not claim unqualified local binaries")

print("ASW repository safety checks: PASS")
