# AmiGuard Signature Workstation (ASW)

AmiGuard Signature Workstation is the isolated analyst workstation for turning submitted Amiga malware samples into evidence-backed signature candidates for AmiGuard and AAA.

ASW is deliberately separate from the public submission service. Public intake ends at quarantine. Samples cross into ASW only through an explicit, verified export/import step.

## Status

M0 established architecture and trust boundaries. M1 implements verified immutable intake. M2 implements deterministic static evidence. M3 defines the isolated visible Amiga runtime lab, historical antivirus suite and native reverse-engineering toolbox; physical N100 runtime qualification remains required. M4 implements structured signature candidates and research-only AmiGuard export. M5 implements ordered qualification gates. M6.1 implements the analyst queue, M6.2 the hash-chained audit trail, M6.3 safe retention cleanup, M6.4 backup/export/disaster-recovery contracts, M6.5 the physical N100 deployment and acceptance runbook, M6.6 makes AmiSandbox the canonical dynamic-analysis backend, and M6.7 adds the executable ASW-to-AmiSandbox runner/evidence adapter.

## Canonical pipeline

```text
Internet -> amiguard.ploos.no quarantine
  -> explicit verified export -> ASW immutable originals
  -> static analysis -> disposable analysis copy
  -> ASW AmiSandbox runner -> AmiSandbox
  -> session.json + events.jsonl + runtime artifacts
  -> ASW hash-bound runtime-evidence manifest
  -> AmiForensics / analyst interpretation
  -> candidate signature -> clean-corpus qualification
  -> visible native AmiGuard qualification -> manual review
  -> research-only signature export -> explicit downstream promotion
```

There is no automatic network path from public quarantine to the analysis runtime. AmiSandbox does not receive signature-publication credentials.

## Dynamic analysis

`Ploos-AS/AmiSandbox` is the required backend whenever ASW claims dynamic malware-analysis evidence. `tools/asw_amisandbox.py` is the ASW-owned runner/evidence boundary: it validates the selected profile and sample hash, launches a configured local AmiSandbox binary without shell interpolation, or safely ingests an already completed analysis directory, then copies and SHA-256 verifies the required raw artifacts into the ASW evidence store and emits an atomic runtime-evidence manifest.

ASW records the exact AmiSandbox build/revision, sample SHA-256, ASW and AmiSandbox machine profiles and retained evidence hashes. Analysis runs default to JIT disabled, guest networking disabled, disposable writable state and no broad writable host filesystem exposure.

The initial runtime matrix covers A500/Kickstart 1.2, A500/Kickstart 1.3, A500+/Kickstart 2.04, A1200/Kickstart 3.0 and A1200/Kickstart 3.1.

## Historical antivirus and native tools

The local reference suite targets lawfully acquired VirusZ III, VirusExecutor, VirusChecker II, VirusSlayer II, Mill and VT-Schutz. M3 also catalogs IRA, ADis, Disassem, Hunk, HunkFunc, SnoopDos, Scout and FileMaster 2.2. Exact binaries, versions, provenance and hashes stay local. Tool verdicts are evidence, not an oracle.

## Operations

M6.1 provides the local analyst workflow. M6.2 provides a tamper-evident JSONL audit chain. M6.3 permits only explicit hash-bound cleanup of disposable workspaces. M6.4 separates normal operational metadata backups from optional malware-bearing immutable-original backups, adds SHA-256 backup manifests and requires restore verification plus an external audit-chain checkpoint. M6.5 defines the dedicated N100 host and physical acceptance contract. M6.6 defines the AmiSandbox integration/evidence contract. M6.7 implements the runner and safe evidence-ingestion boundary used by that contract.

## Milestones

- **M0 — Foundation:** complete.
- **M1 — Intake:** implemented.
- **M2 — Static analysis:** complete with CI.
- **M3 — Isolated runtime analysis:** configuration implemented; physical N100 runtime qualification pending.
- **M4 — Signature candidate pipeline:** implemented; export remains research-only.
- **M5 — Qualification:** ordered evidence-backed gates implemented.
- **M6.1 — Analyst queue:** implemented.
- **M6.2 — Audit trail:** implemented.
- **M6.3 — Retention/cleanup:** implemented.
- **M6.4 — Backup/export/DR:** implemented.
- **M6.5 — N100 deployment runbook:** repository-side implementation complete; physical N100 acceptance pending.
- **M6.6 — AmiSandbox integration:** repository-side contract implemented; physical N100 integration qualification pending.
- **M6.7 — AmiSandbox runner/evidence adapter:** implemented; GitHub CI qualification pending, followed by physical N100 end-to-end qualification.

## Validation

```sh
make check
```

## Safety model

Treat every imported sample as hostile. Analysis copies are disposable. Original bytes remain unchanged and cryptographically identified. AmiSandbox is defense-in-depth and is not treated as the complete host security boundary. No signature becomes a verified AmiGuard detection merely because ASW, AmiSandbox, AmiForensics or a historical antivirus program identifies a sample. Backups containing originals are malware storage and must be handled accordingly. Physical qualification must use visible emulator runs when runtime evidence is claimed.

## License

MIT. See `LICENSE`.
