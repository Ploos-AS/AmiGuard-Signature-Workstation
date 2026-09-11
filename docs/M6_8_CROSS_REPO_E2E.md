# M6.8 — Cross-repo AmiSandbox end-to-end qualification

## Goal

Prove on GitHub Actions that the ASW repository can consume evidence produced by a real AmiSandbox runtime session, not only synthetic fixtures.

## Qualification path

The `AmiSandbox Cross-Repo E2E` workflow:

1. checks out ASW,
2. checks out `Ploos-AS/AmiSandbox` with submodules,
3. records the exact AmiSandbox Git revision,
4. builds AmiSandbox in Release mode with `USE_JIT=OFF` and IPC enabled,
5. launches a real A500 AROS fallback session under Xvfb,
6. verifies `session.json` and `events.jsonl`, including `session.start` and `session.stop`,
7. feeds those real artifacts through `tools/asw_amisandbox.py`,
8. verifies the resulting ASW runtime-evidence manifest and copied artifact hashes, and
9. uploads the complete qualification evidence bundle.

No proprietary Kickstart ROM or Workbench image is required for this CI gate. The sample used by the adapter is a harmless generated sentinel whose SHA-256 is verified before evidence ingestion; it is not malware and is not injected into the guest.

## Security invariants

The gate preserves the ASW/AmiSandbox contract:

- JIT disabled,
- guest networking treated as disabled by policy,
- shared folders disabled by policy,
- exact AmiSandbox revision recorded,
- raw AmiSandbox evidence retained and SHA-256 bound to the ASW manifest,
- no automatic public-quarantine fetch,
- no production signature publication credentials,
- no proprietary ROM material in CI.

## Scope boundary

M6.8 proves cross-repository build/runtime/evidence compatibility on GitHub-hosted Linux runners. It does **not** replace physical N100 qualification with visible runs and the real target Kickstart/Workbench matrix.

It also does not yet prove automatic hostile-sample injection/execution. That remains a later orchestrator milestone and must preserve the explicit verified intake boundary.

## Pass criteria

The milestone passes when the workflow completes successfully and uploads the `asw-m6_8-amisandbox-e2e` artifact containing:

- AmiSandbox `session.json`,
- AmiSandbox `events.jsonl`,
- ASW-copied evidence,
- the ASW runtime-evidence manifest, and
- the AmiSandbox runtime log.
