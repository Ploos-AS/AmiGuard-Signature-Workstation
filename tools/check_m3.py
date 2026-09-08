#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

profiles = json.loads((ROOT / "config" / "emulator-profiles.json").read_text())
tools = json.loads((ROOT / "config" / "reference-tools.json").read_text())

required_profiles = {
    "a500-ks12-68000",
    "a500-ks13-68000",
    "a500plus-os204-68000",
    "a1200-os31-68020",
}
seen = {p["id"] for p in profiles["profiles"]}
missing = required_profiles - seen
if missing:
    raise SystemExit(f"missing emulator profiles: {sorted(missing)}")

for profile in profiles["profiles"]:
    if profile.get("visible") is not True:
        raise SystemExit(f"profile must be visible: {profile['id']}")
    if profile.get("network_default") != "disabled":
        raise SystemExit(f"network must default disabled: {profile['id']}")
    if profile.get("disposable_overlay") is not True:
        raise SystemExit(f"profile must use disposable overlay: {profile['id']}")
    if profile.get("shared_folders_default") != "disabled":
        raise SystemExit(f"shared folders must default disabled: {profile['id']}")

required_av = {"VirusZ III", "VirusExecutor", "VirusChecker II", "VirusSlayer II", "Mill", "VT-Schutz"}
seen_av = {x["name"] for x in tools["historical_antivirus"]}
if required_av - seen_av:
    raise SystemExit(f"missing historical AV tools: {sorted(required_av - seen_av)}")

required_analysis = {"IRA", "ADis", "Disassem", "Hunk", "HunkFunc", "SnoopDos", "Scout", "FileMaster"}
seen_analysis = {x["name"] for x in tools["analysis_tools"]}
if required_analysis - seen_analysis:
    raise SystemExit(f"missing analysis tools: {sorted(required_analysis - seen_analysis)}")

contract = tools["local_install_contract"]
for key in ("record_archive_sha256", "record_binary_sha256", "record_provenance", "record_license"):
    if contract.get(key) is not True:
        raise SystemExit(f"local tool contract must require {key}")
if contract.get("commit_binaries_to_git") is not False:
    raise SystemExit("tool binaries must not be committed to Git")

print("ASW M3 runtime lab contract checks: PASS")
