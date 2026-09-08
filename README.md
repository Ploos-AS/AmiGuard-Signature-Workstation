# AmiGuard Signature Workstation (ASW)

AmiGuard Signature Workstation is the isolated analyst workstation for turning submitted Amiga malware samples into evidence-backed signature candidates for AmiGuard and, later, AAA.

ASW is deliberately separate from the public submission service. Public intake ends at quarantine. Samples cross into ASW only through an explicit, verified export/import step.

## Status

M0 established the architecture, trust boundaries, repository safety contract and CI.

M1 implements verified intake: expected SHA-256 and size are checked before import, original bytes are committed under a digest-derived identity, originals are made read-only, and a machine-readable manifest records provenance without retaining the submitted filename. It also defines the historical antivirus reference suite.

M2 implements deterministic static-analysis evidence for bootblocks, HUNK files and generic files. CI passed on exact M2 HEAD `fcdd57aa0c0cb9b214a4ea80d9b07a2bdf189e24`.

M3 defines the isolated visible Amiga runtime lab: canonical A500/A500+/A1200 profiles, network disabled by default, disposable guest overlays, the historical antivirus suite and a curated native Amiga reverse-engineering/analysis toolbox. M3 repository CI passed; physical N100 runtime qualification remains a separate gate.

M4 implements a structured signature-candidate pipeline. Candidates bind proposed detection logic to an exact sample SHA-256 and evidence references, validate gate ordering, and export research-only metadata following AmiGuard's existing signature conventions. ASW cannot automatically promote a candidate into a verified AmiGuard detection.

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
   +--> evidence
           |
           v
      ASW signature candidate
           |
           v
      AmiGuard research export
           |
           v
      clean-corpus qualification
           |
           v
   visible native AmiGuard qualification
           |
           v
      manual review / promotion decision
```

There is no automatic network path from public quarantine to the analysis runtime.

## Host baseline

The initial physical target is an Intel N100-class mini PC. The design assumes a dedicated Linux host, full-disk encryption where practical, virtualization support, default-deny inbound firewalling, no unrelated production secrets/data, and analysis guests separated from the normal host network.

## Historical antivirus lab and Amiga toolbox

The reference lab targets lawfully acquired historical antivirus software such as VirusZ III, VirusExecutor, VirusChecker II, VirusSlayer II, Mill and VT-Schutz. The native analysis toolbox includes IRA, ADis, Disassem, Hunk, HunkFunc, SnoopDos, Scout and FileMaster 2.2. Their results are evidence, never an oracle. Local binaries must be provenance-recorded and SHA-256 hashed and are not committed here.

See `docs/M1_REFERENCE_ANTIVIRUS_SUITE.md` and `docs/M3_ISOLATED_RUNTIME_LAB.md`.

## M4 candidate workflow

```sh
python3 tools/asw_candidate.py validate examples/candidate.synthetic.json
python3 tools/asw_candidate.py export-amiguard examples/candidate.synthetic.json
```

The export remains `status: research` until AmiGuard's independent qualification and promotion process is complete. See `docs/M4_SIGNATURE_CANDIDATE_PIPELINE.md`.

## Repository content policy

This public repository may contain architecture/docs, schemas, tooling source, synthetic fixtures, hashes, non-sensitive provenance metadata and qualification evidence. It must not contain live malware, infectious payloads, proprietary signature databases without redistribution rights, credentials, infrastructure secrets or private submitter data.

## Planned milestones

- **M0 — Foundation:** complete.
- **M1 — Intake:** verified import and immutable originals; implemented.
- **M2 — Static analysis:** bootblock/HUNK/file evidence pipeline; complete with CI.
- **M3 — Isolated runtime analysis:** emulator/profile/tooling contract complete with CI; physical N100 qualification remains.
- **M4 — Signature candidate pipeline:** structured candidate validation and AmiGuard research export implemented.
- **M5 — Qualification:** clean-corpus regression plus visible native AmiGuard qualification evidence.
- **M6 — Operations:** analyst queue, retention, audit trail, backup/export policy, disaster recovery.

## Validation

```sh
make check
```

## Safety model

Treat every imported sample as hostile. Analysis copies are disposable. Original bytes remain unchanged and are identified by cryptographic hash. No signature becomes a verified AmiGuard detection merely because ASW, a historical antivirus program, or an analyst candidate names a sample.

## License

MIT. See `LICENSE`.
