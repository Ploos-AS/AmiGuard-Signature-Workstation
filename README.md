# AmiGuard Signature Workstation (ASW)

AmiGuard Signature Workstation is the isolated analyst workstation for turning submitted Amiga malware samples into evidence-backed signature candidates for AmiGuard and AAA. The proven Amiga implementation is now also the reference architecture for a broader multi-platform ASW Core with isolated platform backends.

ASW is deliberately separate from the public submission service. Public intake ends at quarantine. Samples cross into ASW only through an explicit, verified export/import step.

## Status

M0 established architecture and trust boundaries. M1 implements verified immutable intake. M2 implements deterministic static evidence. M3 defines the isolated visible Amiga runtime lab, historical antivirus suite and native reverse-engineering toolbox; physical N100 runtime qualification remains required. M4 implements structured signature candidates and research-only AmiGuard export. M5 implements ordered qualification gates. M6.1 implements the analyst queue, M6.2 the hash-chained audit trail, M6.3 safe retention cleanup, M6.4 backup/export/disaster-recovery contracts, M6.5 the physical N100 deployment and acceptance runbook, M6.6 makes AmiSandbox the canonical dynamic-analysis backend, M6.7 adds the executable ASW-to-AmiSandbox runner/evidence adapter, M6.8 qualifies the real cross-repo AmiSandbox/AROS runtime-to-ASW evidence path in GitHub Actions, and M6.9 integrates AmiForensics as the hash-verified downstream report/interpreter stage. M7 extracts a CPU-agnostic ASW Core and defines isolated platform backends.

## Canonical Amiga pipeline

```text
Internet -> amiguard.ploos.no quarantine
  -> explicit verified export -> ASW immutable originals
  -> static analysis -> disposable analysis copy
  -> ASW AmiSandbox runner -> AmiSandbox
  -> session.json + events.jsonl + runtime artifacts
  -> ASW hash-bound runtime-evidence manifest
  -> ASW AmiForensics adapter -> AmiForensics deterministic report
  -> ASW hash-bound AmiForensics analysis manifest
  -> analyst interpretation
  -> candidate signature -> clean-corpus qualification
  -> visible native AmiGuard qualification -> manual review
  -> research-only signature export -> explicit downstream promotion
```

There is no automatic network path from public quarantine to the analysis runtime. AmiSandbox does not receive signature-publication credentials.

## Multi-platform architecture

M7 generalizes custody, evidence, audit, retention and workflow controls into **ASW Core**, while runtime and forensic interpretation remain platform-specific. ASW Core must not assume m68k; the first expansion wave simply focuses on classic m68k systems.

Current platform roadmap:

- **Amiga:** AmiSandbox + AmiForensics — active reference implementation.
- **Atari ST/STE/TT/Falcon:** planned **AtariSandbox**, Hatari-derived; EmuTOS CI path.
- **Macintosh 68k:** planned **MacSandbox**, Basilisk II-derived; lawful local ROM/System Software handling.
- **Sharp X68000:** roadmap **X68kSandbox**; emulator and CI strategy to be selected.
- **NeXT 68k:** roadmap **NeXTSandbox**; workstation/NeXTSTEP evidence model to be designed.
- **Sun-3:** roadmap **Sun3Sandbox**; SunOS/UNIX evidence model to be designed.
- **Sinclair QL:** roadmap **QLSandbox**; QDOS/SMSQ evidence model to be designed.

One dedicated N100-class workstation may initially host the platform workspaces using separate Unix identities, storage roots, emulator builds, queues and disposable runtime images. Cross-platform writable access is deny-by-default. Separate physical machines remain a later hardening option when hostile-sample volume or trust requirements justify reducing blast radius.

A platform listed as `roadmap` is not executable or qualified. Promotion to `active` requires a backend contract, deny-by-default isolation, versioned evidence schema, verified sample/artifact binding, harmless qualification and visible physical qualification before hostile samples are introduced.

See `docs/M7_MULTIPLATFORM_ARCHITECTURE.md` and `docs/M7_2_M7_3_SANDBOX_BACKENDS.md`.

## Dynamic analysis

`Ploos-AS/AmiSandbox` is the required backend whenever ASW claims Amiga dynamic malware-analysis evidence. `tools/asw_amisandbox.py` is the ASW-owned runner/evidence boundary: it validates the selected profile and sample hash, launches a configured local AmiSandbox binary without shell interpolation, or safely ingests an already completed analysis directory, then copies and SHA-256 verifies the required raw artifacts into the ASW evidence store and emits an atomic runtime-evidence manifest.

ASW records the exact AmiSandbox build/revision, sample SHA-256, ASW and AmiSandbox machine profiles and retained evidence hashes. Analysis runs default to JIT disabled, guest networking disabled, disposable writable state and no broad writable host filesystem exposure.

`tools/asw_amiforensics.py` is the downstream interpretation boundary. It verifies all retained AmiSandbox artifact hashes before invoking AmiForensics `workstation/report.py`, then verifies the deterministic AmiForensics report back against the ASW runtime manifest and emits an atomic `asw.amiforensics.analysis` binding manifest containing the exact AmiForensics revision and report hash. This stage reads evidence only; it does not execute samples or authorize signature publication.

The initial Amiga runtime matrix covers A500/Kickstart 1.2, A500/Kickstart 1.3, A500+/Kickstart 2.04, A1200/Kickstart 3.0 and A1200/Kickstart 3.1.

## Historical antivirus and native tools

The local Amiga reference suite targets lawfully acquired VirusZ III, VirusExecutor, VirusChecker II, VirusSlayer II, Mill and VT-Schutz. M3 also catalogs IRA, ADis, Disassem, Hunk, HunkFunc, SnoopDos, Scout and FileMaster 2.2. Exact binaries, versions, provenance and hashes stay local. Tool verdicts are evidence, not an oracle.

## Operations

M6.1 provides the local analyst workflow. M6.2 provides a tamper-evident JSONL audit chain. M6.3 permits only explicit hash-bound cleanup of disposable workspaces. M6.4 separates normal operational metadata backups from optional malware-bearing immutable-original backups, adds SHA-256 backup manifests and requires restore verification plus an external audit-chain checkpoint. M6.5 defines the dedicated N100 host and physical acceptance contract. M6.6 defines the AmiSandbox integration/evidence contract. M6.7 implements the runner and safe evidence-ingestion boundary. M6.8 qualifies the real AmiSandbox cross-repo CI path. M6.9 adds the AmiForensics downstream report boundary. M7 extracts shared controls without rewriting the working Amiga path.

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
- **M6.7 — AmiSandbox runner/evidence adapter:** repository-side implementation and GitHub CI qualification complete; physical N100 end-to-end qualification pending.
- **M6.8 — Cross-repo AmiSandbox E2E:** GitHub Actions qualification PASS using real AmiSandbox build/AROS runtime and ASW evidence ingestion.
- **M6.9 — AmiForensics downstream integration:** repository-side implementation complete; GitHub cross-repo qualification pending.
- **M7.1 — ASW Core extraction:** platform registry and isolation invariants implemented; generic evidence envelope remains next.
- **M7.2 — Atari backend / AtariSandbox:** Hatari-derived analysis backend planned, with EmuTOS CI path.
- **M7.3 — Macintosh 68k backend / MacSandbox:** Basilisk II-derived analysis backend planned; lawful local ROM/System Software runtime qualification required.
- **M7.4 — Unified analyst workflow:** planned after backend contracts stabilize.
- **M7.5 — Sharp X68000:** discovery/backend contract roadmap.
- **M7.6 — NeXT 68k:** discovery/backend contract roadmap.
- **M7.7 — Sun-3:** discovery/backend contract roadmap.
- **M7.8 — Sinclair QL:** discovery/backend contract roadmap.
- **M7.9 — Cross-platform evidence normalization:** planned after platform contracts are defined.

## Validation

```sh
make check
```

## Safety model

Treat every imported sample as hostile. Analysis copies are disposable. Original bytes remain unchanged and cryptographically identified. Emulator instrumentation is defense-in-depth and is not treated as the complete host security boundary. No signature becomes a verified detection merely because an ASW backend, forensic interpreter or historical antivirus program identifies a sample. Backups containing originals are malware storage and must be handled accordingly. Physical qualification must use visible emulator runs when runtime evidence is claimed.

## License

MIT. See `LICENSE`.
