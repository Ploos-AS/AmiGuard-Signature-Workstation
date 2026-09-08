# AmiGuard Signature Workstation (ASW)

AmiGuard Signature Workstation is the isolated analyst workstation for turning submitted Amiga malware samples into evidence-backed signature candidates for AmiGuard and, later, AAA.

ASW is deliberately separate from the public submission service. Public intake ends at quarantine. Samples cross into ASW only through an explicit, verified export/import step.

## Status

M0 established architecture, trust boundaries, repository safety and CI. M1 implements verified immutable intake. M2 implements deterministic static evidence. M3 defines the isolated visible Amiga runtime lab, historical antivirus suite and native reverse-engineering toolbox; physical N100 runtime qualification remains required. M4 implements structured signature candidates and research-only AmiGuard export. M5 implements ordered, evidence-backed clean-corpus, visible native-runtime and manual-review qualification gates.

### Core goals

- receive only explicitly exported quarantine samples
- verify identity and SHA-256 before analysis
- preserve original sample bytes read-only
- never execute samples on the host OS
- keep analysis environments disposable and isolated
- record provenance, analyst observations, candidate signatures, and qualification evidence
- export only reviewable signature metadata/code; never publish live malware samples
- support AmiGuard's independent AmigaOS 1.2+/68000 scanner architecture

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

## Host baseline

The physical target is an Intel N100-class mini PC: dedicated Linux host, full-disk encryption where practical, virtualization support, default-deny inbound firewall, no unrelated production secrets/data, and analysis guests separated from the normal host network.

## Historical antivirus lab

The reference suite targets lawfully acquired copies of VirusZ III, VirusExecutor, VirusChecker II, VirusSlayer II, Mill and VT-Schutz. Their verdicts are evidence, not an oracle. Exact binaries, versions, provenance and hashes stay local. See `docs/M1_REFERENCE_ANTIVIRUS_SUITE.md`.

## Native Amiga analysis toolbox

M3 catalogs IRA, ADis, Disassem, Hunk, HunkFunc, SnoopDos, Scout and FileMaster 2.2 for native 680x0 disassembly, HUNK inspection, tracing, task/resident/interrupt inspection and hex/file/disk analysis. Local binaries are provenance-recorded and SHA-256 hashed, never committed here. See `docs/M3_ISOLATED_RUNTIME_LAB.md`.

## Milestones

- **M0 — Foundation:** complete.
- **M1 — Intake:** implemented.
- **M2 — Static analysis:** complete with CI.
- **M3 — Isolated runtime analysis:** configuration implemented; physical N100 runtime qualification pending.
- **M4 — Signature candidate pipeline:** implemented; export remains research-only.
- **M5 — Qualification:** ordered evidence-backed gates implemented; actual clean-corpus/native evidence is candidate-specific.
- **M6 — Operations:** analyst queue, retention, audit trail, backup/export policy, disaster recovery.

## Validation

```sh
make check
```

## Safety model

Treat every imported sample as hostile. Analysis copies are disposable. Original bytes remain unchanged and cryptographically identified. No signature becomes a verified AmiGuard detection merely because ASW or a historical antivirus program names a sample, and M5 never auto-promotes a signature.

## License

MIT. See `LICENSE`.
