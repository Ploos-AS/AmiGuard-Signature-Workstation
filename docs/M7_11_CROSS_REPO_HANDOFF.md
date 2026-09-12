# M7.11 — Cross-repo quarantine-to-ASW handoff qualification

This milestone qualifies the complete non-executing handoff path between the public AmiGuard quarantine and the platform-specific ASW intake.

## Scope

The qualification uses the real `amiguard-admin` implementation from `Ploos-AS/AmiGuard-Infrastructure` and the real `asw_route_import.py` implementation from this repository.

For each supported platform, CI performs:

1. create a harmless schema-v2 quarantine record and sample;
2. run `amiguard-admin route` against that quarantine;
3. validate the produced routing manifest and platform namespace;
4. import the routed sample through ASW's independent verification boundary;
5. confirm immutable original storage, queue registration, and acknowledgement;
6. confirm `analysis_started` remains `false` throughout the handoff.

Platforms covered:

- `amiga` -> ASW namespace `amiga`
- `atari-st` -> ASW namespace `atari`
- `mac68k` -> ASW namespace `mac68k`

## Tamper gate

CI also routes a valid harmless Atari ST fixture, modifies the handoff sample after routing, and requires ASW to reject it before queue registration. This proves that the second verification boundary is independent of the public-side export check.

## Trust boundary

A successful handoff means only that the sample identity and routing metadata survived quarantine export and ASW import. It does not mean the sample is malware, analysed, classified, approved, signed, or publishable. No emulator or sandbox is launched by this qualification.

## CI

`.github/workflows/route-e2e.yml` checks out both repositories, builds `amiguard-admin`, and runs:

`python3 tools/qualify_route_e2e.py --admin ../amiguard-admin`

The milestone is PASS only when the cross-repo workflow succeeds for all three platform fixtures and the post-route tamper rejection gate.
