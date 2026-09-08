# AmiGuard Signature Workstation (ASW)

AmiGuard Signature Workstation is the isolated analyst workstation for turning submitted Amiga malware samples into evidence-backed signature candidates for AmiGuard and, later, AAA.

ASW is deliberately separate from the public submission service. Public intake ends at quarantine. Samples cross into ASW only through an explicit, verified export/import step.

## Status

M0 established the architecture, trust boundaries, repository safety contract and CI. M0 CI passed on exact HEAD `cd742241f6976d783eda86623d82350bf63f5e87`.

M1 implements the first verified intake workflow: expected SHA-256 and size are checked before import, original bytes are committed under a digest-derived identity, originals are made read-only, and a machine-readable manifest records provenance without retaining the submitted filename. M1 also defines the reference-antivirus lab inventory that later isolated Amiga emulation will use for historical identification evidence.

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
   |              |
   |              +--> historical antivirus reference suite
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

There is no automatic network path from the public quarantine to the analysis runtime.

## Host baseline

The initial physical target is an Intel N100-class mini PC. The design assumes:

- Linux host
- full-disk encryption where practical
- dedicated ASW use
- virtualization support enabled
- no production secrets or unrelated personal data
- host firewall default-deny inbound
- analysis guests/containers separated from the normal host network
- removable/export storage treated as hostile-content media

The exact host distribution and emulator/hypervisor deployment are qualified in later milestones.

## Sample lifecycle

```text
submitted
  -> admin verified
  -> explicitly exported
  -> imported to ASW
  -> SHA/provenance verified
  -> original sealed
  -> analysis copy created
  -> analysed
  -> historical AV evidence when useful
  -> candidate signature
  -> clean-corpus qualification
  -> visible A500/68000/Kickstart 1.2 runtime qualification
  -> reviewed
  -> eligible for AmiGuard signature integration
```

Every transition that changes trust level must be explicit and recorded.

## M1 intake

A verified import can be exercised with a harmless fixture:

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

## Reference antivirus lab

Historical antivirus programs can provide valuable naming and family-identification evidence for old Amiga samples. ASW therefore plans an isolated emulator reference suite containing lawfully acquired copies of tools such as VirusZ III, VirusExecutor, VirusChecker II, VirusSlayer II, Mill and VT-Schutz across appropriate Kickstart/AmigaOS profiles.

Their verdicts are **evidence, not an oracle**. A historical scanner result alone never creates an AmiGuard signature. Exact tool binaries, provenance, versions and hashes must be recorded locally, and the software itself is not committed to this repository. See `docs/M1_REFERENCE_ANTIVIRUS_SUITE.md`.

## Repository content policy

This public repository may contain architecture/docs, schemas, tooling source, synthetic fixtures, hashes, non-sensitive provenance metadata and qualification evidence. It must not contain live malware, infectious payloads, proprietary signature databases without redistribution rights, credentials, infrastructure secrets or private submitter data.

## Planned milestones

- **M0 — Foundation:** architecture, trust boundaries, sample lifecycle, repository safety contract, initial CI. **Complete.**
- **M1 — Intake:** verified import manifest, immutable-original workflow and historical antivirus reference-lab contract. **Implemented; CI/host qualification gates apply.**
- **M2 — Static analysis:** deterministic metadata, Amiga file/HUNK/bootblock inspection helpers, evidence bundle.
- **M3 — Isolated runtime analysis:** disposable Amiga emulation workflow, reference antivirus images and network disabled by default.
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
