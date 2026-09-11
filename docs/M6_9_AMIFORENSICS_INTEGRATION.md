# M6.9 — AmiForensics downstream integration

## Goal

Make AmiForensics the canonical downstream interpreter/report generator for ASW-owned AmiSandbox runtime evidence without allowing AmiForensics to execute submitted samples or publish signatures.

## Boundary

ASW owns sample identity, runtime orchestration, evidence retention and trust decisions. AmiSandbox owns low-level dynamic execution evidence. AmiForensics reads already-retained evidence and produces analysis/report artifacts. AmiGuard/AAA promotion remains a separate explicit process.

Canonical flow:

```text
verified ASW sample
  -> AmiSandbox runtime
  -> ASW runtime-evidence manifest + retained session.json/events.jsonl
  -> ASW AmiForensics adapter
  -> AmiForensics workstation/report.py
  -> verified amiforensics.workstation.report/1
  -> ASW AmiForensics binding manifest
  -> analyst/candidate pipeline
```

## Adapter contract

`tools/asw_amiforensics.py`:

1. requires an `asw.amisandbox.runtime-evidence` manifest;
2. verifies every retained artifact against its ASW SHA-256 before invoking AmiForensics;
3. requires `session.json` and `events.jsonl`;
4. invokes the configured AmiForensics report tool with `subprocess.run()` and no shell interpolation;
5. never executes a sample;
6. requires report schema `amiforensics.workstation.report/1`;
7. verifies the report's runtime-manifest SHA-256 and full evidence-name/hash set back against ASW evidence;
8. writes an atomic `asw.amiforensics.analysis` binding manifest containing sample identity, runtime-manifest SHA-256, exact AmiForensics revision, report schema and report SHA-256.

AmiForensics interpretation is evidence, not an automatic malware verdict and not authorization to publish a signature.

## CI qualification

Repository CI uses a synthetic report-tool fixture to exercise trust-boundary validation. Cross-repo E2E extends the existing real AmiSandbox/AROS workflow by checking out `Ploos-AS/AmiForensics`, running its actual `workstation/report.py` against real AmiSandbox runtime evidence, and verifying the resulting report/binding manifest.

No proprietary ROM or malware sample is required for this CI gate. Physical N100 qualification with visible runtime remains separate.
