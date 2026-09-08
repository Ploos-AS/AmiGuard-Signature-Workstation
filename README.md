# AmiGuard Signature Workstation (ASW)

AmiGuard Signature Workstation is the isolated analyst workstation for turning submitted Amiga malware samples into evidence-backed signature candidates for AmiGuard and, later, AAA.

ASW is deliberately separate from the public submission service. Public intake ends at quarantine. Samples cross into ASW only through an explicit, verified export/import step.

## M0 status

M0 establishes the architecture, trust boundaries, repository contract, and initial qualification plan for an Intel N100-class workstation.

### Core goals

- receive only explicitly exported quarantine samples
- verify identity and SHA-256 before analysis
- preserve original sample bytes read-only
- never execute samples on the host OS
- keep analysis environments disposable and isolated
- record provenance, analyst observations, candidate signatures, and qualification evidence
- export only reviewable signature metadata/code; never publish live malware samples
- support AmiGuard's independent AmigaOS 1.2+/68000 scanner architecture

### Non-goals

ASW is not:

- a public upload endpoint
- a malware distribution archive
- a replacement for AmiGuard-Infrastructure
- an automatic malware execution farm
- a generic sandbox for arbitrary modern malware
- a reason to weaken the public write-only quarantine boundary

## Trust boundary

```text
Internet
   |
   v
amiguard.ploos.no
AmiGuard-Infrastructure quarantine
   |
   | explicit admin export
   | SHA-256 + metadata verification
   v
TRANSFER MEDIA / CONTROLLED IMPORT
   |
   v
ASW intake
   |
   +--> immutable originals
   |
   +--> disposable analysis copies
   |       |
   |       +--> static analysis
   |       +--> filesystem/image inspection
   |       +--> Amiga emulation when needed
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

No automatic network path from the public quarantine to the analysis runtime is required for M0.

## Host baseline

The initial physical target is an Intel N100-class mini PC. M0 assumes:

- Linux host
- full-disk encryption where practical
- dedicated ASW use
- virtualization support enabled
- no production secrets or unrelated personal data
- host firewall default-deny inbound
- analysis guests/containers separated from the normal host network
- removable/export storage treated as hostile-content media

The exact distribution and hypervisor/container stack are intentionally deferred to M1 qualification.

## Sample lifecycle

A sample is not considered analysis-ready merely because it exists in public quarantine.

The intended lifecycle is:

```text
submitted
  -> admin verified
  -> explicitly exported
  -> imported to ASW
  -> SHA/provenance verified
  -> original sealed
  -> analysis copy created
  -> analysed
  -> candidate signature
  -> clean-corpus qualification
  -> visible A500/68000/Kickstart 1.2 runtime qualification
  -> reviewed
  -> eligible for AmiGuard signature integration
```

Every transition that changes trust level must be explicit and recorded.

## Repository content policy

This public repository may contain:

- architecture and operations documentation
- schemas
- tooling source code
- synthetic fixtures
- hashes and non-sensitive provenance metadata
- candidate signature metadata that does not contain redistributable malware bytes
- qualification evidence

This repository must not contain:

- live malware samples
- extracted infectious payloads
- proprietary signature databases without redistribution rights
- credentials or infrastructure secrets
- unredacted private submitter data

## Planned milestones

- **M0 — Foundation:** architecture, trust boundaries, sample lifecycle, repository safety contract, initial CI.
- **M1 — Intake:** verified import manifest and immutable-original workflow.
- **M2 — Static analysis:** deterministic metadata, Amiga file/HUNK/bootblock inspection helpers, evidence bundle.
- **M3 — Isolated runtime analysis:** disposable Amiga emulation workflow with network disabled by default.
- **M4 — Signature candidate pipeline:** structured candidate metadata and compiler/export integration for AmiGuard.
- **M5 — Qualification:** clean-corpus regression plus visible native AmiGuard qualification evidence.
- **M6 — Operations:** analyst queue, retention, audit trail, backup/export policy, disaster recovery.

## Validation

M0 uses lightweight repository checks only:

```sh
make check
```

## Safety model

Treat every imported sample as hostile, even when it appears to be a harmless test file. Analysis copies are disposable. Original bytes remain unchanged and are identified by cryptographic hash.

No signature becomes a verified AmiGuard detection merely because ASW generated it. Sample-backed analysis, clean-corpus qualification, and visible native runtime evidence remain separate gates.

## License

MIT. See `LICENSE`.
