# M6.6 — AmiSandbox integration contract

M6.6 makes AmiSandbox the canonical dynamic-analysis backend for AmiGuard Signature Workstation (ASW).

## Goal

ASW is the orchestrator and trust/promotion boundary. AmiSandbox is the component that executes suspicious Amiga code and emits deterministic, machine-readable runtime evidence. AmiForensics and analyst tooling interpret that evidence. No emulator verdict directly promotes a signature.

## Canonical flow

```text
amiguard.ploos.no quarantine
        |
        v
verified ASW intake
        |
        v
immutable original -> disposable analysis copy
        |
        v
AmiSandbox analysis session
        |
        +-- session.json
        +-- events.jsonl
        +-- screenshots / dumps / hashes / traces
        |
        v
AmiForensics + analyst review
        |
        v
candidate signature
        |
        v
clean-corpus + native AmiGuard qualification
        |
        v
manual approval / research-only export
```

## Backend contract

ASW dynamic-evidence runs MUST:

- use `Ploos-AS/AmiSandbox`;
- record the exact AmiSandbox Git revision/build identity;
- use analysis mode with a fresh per-run `AMISANDBOX_ANALYSIS_DIR`;
- use a profile mapped in `config/emulator-profiles.json`;
- disable JIT;
- disable guest networking by default;
- avoid broad writable host filesystem exposure;
- use disposable guest writable state;
- preserve `session.json` and `events.jsonl`;
- hash retained evidence artifacts;
- associate artifacts with ASW sample ID and immutable-original SHA-256;
- destroy disposable guest state after the run unless explicitly retained as hostile evidence.

## Initial profile contract

ASW tracks the five initial AmiSandbox analysis targets:

1. A500 / Kickstart 1.2
2. A500 / Kickstart 1.3
3. A500+ / Kickstart 2.04
4. A1200 / Kickstart 3.0
5. A1200 / Kickstart 3.1

Local ROM/OS material is not part of Git and must have lawful provenance plus local SHA-256 inventory.

## Evidence ingestion

M6.6 initially requires ASW to understand the stable envelope around an AmiSandbox run rather than every future event type. `session.json` and `events.jsonl` are retained verbatim and hashed. ASW tooling may later normalize selected events into its own evidence schema while preserving the original AmiSandbox artifacts.

Unknown future AmiSandbox JSONL event classes must not make the raw evidence invalid. Consumers should tolerate event-model extension and use the version fields supplied by AmiSandbox.

## Security boundary

AmiSandbox is not considered a complete host security boundary. ASW retains responsibility for:

- hostile-sample transfer discipline;
- immutable originals;
- host hardening;
- filesystem permissions;
- network policy;
- disposable workspaces;
- audit logging;
- evidence integrity;
- candidate qualification;
- manual promotion decisions.

AmiSandbox must never receive production credentials or a direct publication credential for AmiGuard/AAA signatures.

## Relationship to AmiForensics

AmiSandbox emits low-level dynamic evidence. AmiForensics is the preferred downstream analysis layer for interpreting runtime artifacts alongside static/reverse-engineering evidence. ASW owns the association between the sample, AmiSandbox session, AmiForensics output, candidate signature and qualification state.

## Qualification

Repository-side M6.6 is complete when:

- `config/emulator-profiles.json` declares AmiSandbox as required backend;
- M3 documents the AmiSandbox evidence boundary;
- the N100 deployment runbook requires AmiSandbox;
- ASW documentation names the canonical pipeline;
- repository validation accepts the updated profile schema.

Physical M6.6 qualification remains pending until the actual N100 workstation demonstrates a harmless visible AmiSandbox run that produces `session.json` and `events.jsonl`, those artifacts are ingested into ASW evidence storage with verified hashes, and disposable guest state is destroyed.
