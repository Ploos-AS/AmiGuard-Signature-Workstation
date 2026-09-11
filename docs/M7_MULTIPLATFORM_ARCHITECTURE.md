# M7 — Multi-platform ASW architecture

## Goal

Generalize the proven AmiGuard Signature Workstation architecture so one dedicated analysis host can safely operate independent Amiga, Atari ST and 68k Macintosh malware-analysis workspaces without merging their corpora, runtime state or platform-specific interpretation logic.

The existing Amiga path remains the reference implementation. M7 does not weaken or replace any existing Amiga qualification gate.

## Architecture

ASW is split conceptually into two layers:

1. **ASW Core** — platform-neutral custody, evidence and workflow controls.
2. **Platform backends** — platform-specific emulator, machine profiles, evidence interpretation, native tools and signature/export logic.

### ASW Core responsibilities

The following controls are platform-neutral and should converge on shared schemas/tools rather than be reimplemented independently:

- verified import and SHA-256 sample identity
- immutable originals
- disposable analysis copies
- analyst queue and state transitions
- append-only/hash-chained audit
- evidence manifests and artifact hashing
- retention and cleanup
- backup/export/restore verification
- explicit approval gates
- research-only candidate state
- exact backend revision/build recording
- deterministic run identifiers
- host isolation policy

### Platform backend responsibilities

Each backend owns:

- supported machine matrix
- emulator build and analysis instrumentation
- ROM/OS identity and provenance
- guest ingress method
- runtime event schema
- platform-specific static/dynamic interpretation
- native reverse-engineering tools
- clean corpus
- signature format and downstream consumer

## Initial backends

| Platform | Runtime backend | Free CI firmware/OS path | Downstream interpretation |
| --- | --- | --- | --- |
| Amiga | AmiSandbox (Amiberry-derived) | AROS | AmiForensics |
| Atari ST/STE | planned AtariSandbox (Hatari-derived) | EmuTOS | planned Atari-specific forensics layer |
| Macintosh 68k | planned MacSandbox (Basilisk II-derived) | no equivalent production-compatible free ROM assumption; CI scope must be designed separately | planned Mac-specific forensics layer |

## Host layout

One dedicated N100-class workstation may initially host all three platforms provided the logical boundaries below are enforced:

```text
/opt/asw/
  core/
  amiga/
  atari/
  mac68k/

/var/lib/asw/
  amiga/
    originals/
    evidence/
    candidates/
    work/
  atari/
    originals/
    evidence/
    candidates/
    work/
  mac68k/
    originals/
    evidence/
    candidates/
    work/
```

Each platform should use a distinct unprivileged service/user identity, separate writable roots, separate emulator builds and separate queues. Cross-platform artifact access is deny-by-default.

## Isolation policy

A single physical host is acceptable for the initial lab because the emulator workloads are light compared with the available x86-64 resources. The important boundary is not CPU capacity but containment and evidence provenance.

Required controls:

- no shared writable guest folders
- no external guest networking by default
- disposable writable disk overlays/images
- explicit sample ingress and artifact egress
- separate Unix identities per platform
- platform-specific storage roots
- no automatic cross-platform corpus sharing
- no signing/publication credentials inside emulator runtimes
- emulator revision/build pinned in every run manifest
- visible local qualification for physical runtime claims

Move to separate physical machines when hostile-sample volume, trust requirements or operational exposure justify reducing cross-platform blast radius. A future high-assurance deployment may therefore use one host per platform while retaining the same ASW Core contracts.

## Migration rule

Do not rewrite the working Amiga stack merely to obtain code reuse. Extract platform-neutral contracts incrementally from proven behavior. Compatibility with existing `asw.amisandbox.runtime-evidence` and `asw.amiforensics.analysis` evidence must be preserved.

## Milestone outline

### M7.1 — Core contract extraction

- identify generic sample/evidence/run identifiers
- define `asw.runtime-evidence/1` envelope with platform/backend fields
- preserve Amiga compatibility adapter
- define platform namespace and storage policy
- add tests rejecting cross-platform artifact confusion

### M7.2 — Atari backend contract

- establish Hatari-derived `AtariSandbox`
- EmuTOS CI profile
- ST/STE initial machine matrix
- deterministic JSON/JSONL runtime evidence
- no host-write/network defaults
- ASW adapter and cross-repo harmless CI qualification

### M7.3 — Macintosh 68k backend contract

- establish Basilisk II-derived `MacSandbox`
- define lawful ROM/System Software handling and CI limits
- Classic/Mac II initial machine matrix
- deterministic JSON/JSONL runtime evidence
- no host-write/network defaults
- ASW adapter and harmless qualification path

### M7.4 — Unified analyst workflow

- common queue surface
- platform-specific interpreter dispatch
- shared audit/retention/backup machinery
- explicit platform labels in every candidate and export

## Non-goals

M7 does not make malware portable across platforms, does not merge signature formats, and does not allow a verdict from one platform to authorize a release on another. Shared infrastructure is for custody and reproducibility; analysis semantics remain platform-specific.
