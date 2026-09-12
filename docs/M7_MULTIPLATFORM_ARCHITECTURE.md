# M7 — Multi-platform ASW architecture

## Goal

Generalize the proven AmiGuard Signature Workstation architecture so one dedicated analysis host can safely operate independent malware-analysis workspaces for multiple classic platforms without merging their corpora, runtime state or platform-specific interpretation logic.

The existing Amiga path remains the reference implementation. M7 does not weaken or replace any existing Amiga qualification gate.

ASW Core is intentionally CPU-agnostic. The first expansion family happens to be Motorola 68k systems, but no core schema or workflow may assume that every future platform is m68k.

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
- explicit platform and backend identity in every runtime/evidence record

### Platform backend responsibilities

Each backend owns:

- supported machine matrix
- emulator build and analysis instrumentation
- ROM/firmware/OS identity and provenance
- guest ingress method
- runtime event schema
- platform-specific static/dynamic interpretation
- native reverse-engineering tools
- clean corpus
- signature format and downstream consumer

## Platform roadmap

| Priority | Platform | Runtime backend | Emulator base | CI/free OS path | State |
| ---: | --- | --- | --- | --- | --- |
| 1 | Amiga | AmiSandbox | Amiberry-derived | AROS | active/reference |
| 2 | Atari ST/STE/TT/Falcon | AtariSandbox | Hatari-derived | EmuTOS | planned M7.2 |
| 3 | Macintosh 68k | MacSandbox | Basilisk II-derived | to be designed; no assumption of a production-compatible free Apple ROM | planned M7.3 |
| 4 | Sharp X68000 | X68kSandbox | emulator base to be selected | to be researched | roadmap M7.5 |
| 5 | NeXT 68k | NeXTSandbox | emulator base to be selected | to be researched | roadmap M7.6 |
| 6 | Sun-3 | Sun3Sandbox | emulator base to be selected | to be researched | roadmap M7.7 |
| 7 | Sinclair QL | QLSandbox | emulator base to be selected | to be researched | roadmap M7.8 |

The ordering is deliberate. Atari and Mac receive first-class implementations first. X68000 is the next personal-computer target because its analysis model is closest to the current disk/file-oriented workflow. NeXT and Sun-3 then extend ASW into m68k workstation/UNIX analysis. QL remains a useful lower-volume target after those foundations exist.

A platform with `status: roadmap` must not be treated as executable or qualified merely because it exists in `config/platforms.json`. Activation requires an explicit backend contract, isolation review, evidence schema, harmless runtime qualification and platform-specific interpretation path.

## Host layout

One dedicated N100-class workstation may initially host all platforms provided logical boundaries are enforced:

```text
/opt/asw/
  core/
  amiga/
  atari/
  mac68k/
  x68000/
  next68k/
  sun3/
  ql/

/var/lib/asw/
  amiga/{originals,evidence,candidates,work}/
  atari/{originals,evidence,candidates,work}/
  mac68k/{originals,evidence,candidates,work}/
  x68000/{originals,evidence,candidates,work}/
  next68k/{originals,evidence,candidates,work}/
  sun3/{originals,evidence,candidates,work}/
  ql/{originals,evidence,candidates,work}/
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

### M7.5 — Sharp X68000 discovery and backend contract

- select and license-review the emulator base
- define Human68k-compatible machine/runtime matrix
- define disk, boot, filesystem and process/event evidence model
- research CI-safe firmware/OS strategy
- establish `X68kSandbox` only after the contract is accepted

### M7.6 — NeXT 68k discovery and backend contract

- select emulator base for 68030/68040 NeXT systems
- define Mach/NeXTSTEP process, filesystem and executable evidence model
- define lawful ROM/OS handling
- evaluate harmless automated runtime qualification

### M7.7 — Sun-3 discovery and backend contract

- select emulator base for Sun-3 hardware
- define SunOS/UNIX process, filesystem, network and executable evidence model
- preserve network-off-by-default even though the historical platform is network-centric
- define deterministic disk-image and runtime qualification strategy

### M7.8 — Sinclair QL discovery and backend contract

- select emulator base for 68008 QL systems
- define QDOS/SMSQ-oriented evidence requirements
- establish disk/microdrive image handling and harmless runtime qualification

### M7.9 — Cross-platform evidence normalization

- normalize the platform-neutral envelope only
- retain native backend event streams verbatim
- support common analyst queries without erasing platform semantics
- prove that evidence/candidates cannot be rebound to another platform namespace

## Activation gate for every new platform

A roadmap platform becomes `planned` only after its emulator/base and legal asset model are documented. It becomes `active` only after all of the following pass:

1. backend repository and pinned build/revision exist;
2. platform-specific machine profiles are defined;
3. networking and host-write defaults are deny-by-default;
4. sample ingress and disposable-state destruction are specified;
5. `session.json`/`events.jsonl` or an equivalent versioned evidence contract is implemented;
6. ASW verifies sample, platform, backend and artifact hashes;
7. harmless CI/runtime qualification passes where legally/technically possible;
8. visible physical qualification passes before hostile samples are used;
9. downstream interpretation cannot directly authorize publication/signing.

## Non-goals

M7 does not make malware portable across platforms, does not merge signature formats, and does not allow a verdict from one platform to authorize a release on another. Shared infrastructure is for custody and reproducibility; analysis semantics remain platform-specific.
