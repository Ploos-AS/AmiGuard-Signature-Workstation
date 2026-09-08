# AmiGuard Signature Workstation (ASW)

AmiGuard Signature Workstation is the isolated analyst workstation for turning submitted Amiga malware samples into evidence-backed signature candidates for AmiGuard and, later, AAA.

ASW is deliberately separate from the public submission service. Public intake ends at quarantine. Samples cross into ASW only through an explicit, verified export/import step.

## Status

M0 established architecture and trust boundaries. M1 implements verified immutable intake. M2 implements deterministic static evidence. M3 defines the isolated visible Amiga runtime lab, historical antivirus suite and native reverse-engineering toolbox; physical N100 runtime qualification remains required. M4 implements structured signature candidates and research-only AmiGuard export. M5 implements ordered qualification gates. M6.1 implements the analyst queue. M6.2 implements an append-only, hash-chained audit trail.

## Trust boundary

```text
Internet -> amiguard.ploos.no quarantine
  -> explicit verified export -> ASW immutable originals
  -> static analysis -> disposable visible Amiga runtime
  -> candidate signature -> clean-corpus qualification
  -> visible native AmiGuard qualification -> manual review
  -> research-only AmiGuard export
```

There is no automatic network path from public quarantine to the analysis runtime.

## Historical antivirus and native tools

The local reference suite targets lawfully acquired VirusZ III, VirusExecutor, VirusChecker II, VirusSlayer II, Mill and VT-Schutz. M3 also catalogs IRA, ADis, Disassem, Hunk, HunkFunc, SnoopDos, Scout and FileMaster 2.2. Exact binaries, versions, provenance and hashes stay local. Tool verdicts are evidence, not an oracle.

## Operations

M6.1 provides the local workflow `imported -> static-analysis -> [runtime-analysis] -> candidate -> qualification -> reviewed -> closed`, plus explicit terminal rejection. M6.2 adds a separate JSONL audit trail whose events are chained by SHA-256. The audit chain is tamper-evident rather than tamper-proof and is verified before append/backup/restore.

## Milestones

- **M0 — Foundation:** complete.
- **M1 — Intake:** implemented.
- **M2 — Static analysis:** complete with CI.
- **M3 — Isolated runtime analysis:** configuration implemented; physical N100 runtime qualification pending.
- **M4 — Signature candidate pipeline:** implemented; export remains research-only.
- **M5 — Qualification:** ordered evidence-backed gates implemented.
- **M6.1 — Analyst queue:** implemented.
- **M6.2 — Audit trail:** implemented.
- **M6.3 — Retention/cleanup:** next.
- **M6.4 — Backup/export/DR:** planned.
- **M6.5 — N100 deployment runbook:** planned.

## Validation

```sh
make check
```

## Safety model

Treat every imported sample as hostile. Analysis copies are disposable. Original bytes remain unchanged and cryptographically identified. No signature becomes a verified AmiGuard detection merely because ASW or a historical antivirus program names a sample. Audit records never contain malware bytes.

## License

MIT. See `LICENSE`.
