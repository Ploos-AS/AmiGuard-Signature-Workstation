# AmiGuard Signature Workstation (ASW)

AmiGuard Signature Workstation is the isolated analyst workstation for turning submitted Amiga malware samples into evidence-backed signature candidates for AmiGuard and, later, AAA.

ASW is deliberately separate from the public submission service. Public intake ends at quarantine. Samples cross into ASW only through an explicit, verified export/import step.

## Status

M0 established the architecture, trust boundaries, repository safety contract and CI.

M1 implements verified intake: expected SHA-256 and size are checked before import, original bytes are committed under a digest-derived identity, originals are made read-only, and a machine-readable manifest records provenance without retaining the submitted filename. It also defines the historical antivirus reference suite.

M2 implements deterministic static-analysis evidence for bootblocks, HUNK files and generic files. CI passed on exact M2 HEAD `fcdd57aa0c0cb9b214a4ea80d9b07a2bdf189e24`.

M3 defines the isolated visible Amiga runtime lab: canonical A500/A500+/A1200 profiles, network disabled by default, disposable guest overlays, the historical antivirus suite and a curated native Amiga reverse-engineering/analysis toolbox. Repository configuration is CI-testable; actual runtime qualification remains a physical-ASW gate.

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
Internet
   |
   v
amiguard.ploos.no quarantine
   |
   | explicit verified export
   v
ASW immutable originals
   |
   +--> deterministic static analysis
   |
   +--> disposable visible Amiga runtime
   |       |
   |       +--> historical antivirus suite
   |       +--> native reverse-engineering toolbox
   |
   +--> evidence + candidate signature
           |
           v
      clean-corpus qualification
           |
           v
   visible native AmiGuard qualification
           |
           v
      reviewed signature output
```

There is no automatic network path from public quarantine to the analysis runtime.

## Host baseline

The initial physical target is an Intel N100-class mini PC. The design assumes a dedicated Linux host, full-disk encryption where practical, virtualization support, default-deny inbound firewalling, no unrelated production secrets/data, and analysis guests separated from the normal host network.

## Sample lifecycle

```text
submitted
  -> admin verified
  -> explicitly exported
  -> imported to ASW
  -> SHA/provenance verified
  -> original sealed
  -> static evidence
  -> disposable runtime analysis when needed
  -> historical AV / reverse-engineering evidence
  -> candidate signature
  -> clean-corpus qualification
  -> visible A500/68000/Kickstart 1.2 runtime qualification
  -> reviewed
  -> eligible for AmiGuard signature integration
```

## M1 intake

```sh
python3 tools/asw_intake.py import \
  --root /path/to/private/asw-data \
  --sample /path/to/exported.sample \
  --submission-id 0123456789abcdef0123456789abcdef \
  --expected-sha256 <sha256> \
  --expected-size <bytes> \
  --provenance 'AmiGuard public quarantine export'
```

The private ASW data root is intentionally outside this Git repository.

## Historical antivirus lab

The initial reference suite targets lawfully acquired copies of VirusZ III, VirusExecutor, VirusChecker II, VirusSlayer II, Mill and VT-Schutz. Their verdicts are evidence, not an oracle. Exact binaries, versions, provenance and hashes are recorded locally and are not committed here. See `docs/M1_REFERENCE_ANTIVIRUS_SUITE.md`.

## Native Amiga analysis toolbox

M3 also adds a curated analysis/reverse-engineering catalog. Initial Aminet references include IRA, ADis, Disassem, Hunk, HunkFunc, SnoopDos, Scout and FileMaster 2.2. This gives ASW native tools for 680x0 disassembly/reassembly, HUNK inspection, DOS/library/device tracing, task/resident/interrupt inspection and hex/file/disk analysis. FileMaster 2.2 is especially useful because it supports AmigaOS 1.2+, while several of the more advanced tools target OS 2.x+.

All local tool archives/binaries must be provenance-recorded and SHA-256 hashed. Binaries are never committed to this public repository. See `docs/M3_ISOLATED_RUNTIME_LAB.md`, `config/reference-tools.json` and `config/emulator-profiles.json`.

## Repository content policy

This public repository may contain architecture/docs, schemas, tooling source, synthetic fixtures, hashes, non-sensitive provenance metadata and qualification evidence. It must not contain live malware, infectious payloads, proprietary signature databases without redistribution rights, credentials, infrastructure secrets or private submitter data.

## Planned milestones

- **M0 — Foundation:** complete.
- **M1 — Intake:** verified import and immutable originals; implemented.
- **M2 — Static analysis:** bootblock/HUNK/file evidence pipeline; complete with CI.
- **M3 — Isolated runtime analysis:** emulator/profile/tooling contract implemented; physical N100 runtime qualification still required.
- **M4 — Signature candidate pipeline:** structured candidate metadata and compiler/export integration for AmiGuard.
- **M5 — Qualification:** clean-corpus regression plus visible native AmiGuard qualification evidence.
- **M6 — Operations:** analyst queue, retention, audit trail, backup/export policy, disaster recovery.

## Validation

```sh
make check
```

## Safety model

Treat every imported sample as hostile. Analysis copies are disposable. Original bytes remain unchanged and are identified by cryptographic hash. No signature becomes a verified AmiGuard detection merely because ASW or a historical antivirus program names a sample.

## License

MIT. See `LICENSE`.
