# M6.7 — AmiSandbox runner and evidence adapter

M6.7 turns the M6.6 integration contract into an executable ASW-side adapter.

## Scope

`tools/asw_amisandbox.py` is the ASW-owned boundary around AmiSandbox execution and evidence ingestion. It does not download samples, ROMs, operating-system images, or emulator binaries. It consumes an already verified ASW sample and either:

1. launches a configured local AmiSandbox executable with an ASW-selected profile, or
2. validates and ingests an already completed AmiSandbox analysis directory with `--ingest-only`.

The second mode is used by repository CI so no proprietary ROM or hostile sample is needed on a GitHub-hosted runner.

## Required safety properties

The adapter:

- validates `config/emulator-profiles.json` schema version 2;
- requires `amisandbox` as the configured runtime backend;
- refuses profiles that do not disable JIT, networking, and shared folders by default;
- hashes the disposable sample and optionally verifies an expected SHA-256;
- refuses symlink samples;
- launches AmiSandbox without `shell=True` or shell interpolation;
- creates a fresh analysis directory for execution mode;
- sets `AMISANDBOX_ANALYSIS_DIR`, `AMISANDBOX_MACHINE_PROFILE`, and `AMISANDBOX_CONFIG_FINGERPRINT`;
- requires `session.json` and `events.jsonl`;
- refuses evidence files that are symlinks, non-regular files, path escapes, or larger than the configured safety bound;
- validates JSON syntax but otherwise treats AmiSandbox event records as opaque/versioned raw evidence;
- copies evidence into a new ASW evidence directory with exclusive-create semantics;
- verifies SHA-256 again after each evidence copy;
- writes an atomic ASW runtime-evidence manifest.

## Runtime evidence manifest

The manifest binds at minimum:

- ASW sample ID;
- sample SHA-256;
- AmiSandbox revision and build identity;
- ASW profile ID;
- mapped AmiSandbox profile ID;
- JIT/network/shared-folder policy;
- visible-runtime policy;
- start/end timestamps;
- artifact names, byte sizes, paths, and SHA-256 hashes.

The initial manifest kind is:

```text
asw.amisandbox.runtime-evidence
```

## CI qualification

`tests/test_amisandbox.py` uses harmless synthetic files to prove the adapter contract without requiring a ROM, Workbench image, or malware sample. It verifies successful evidence ingestion and hash binding, rejection of a wrong sample hash, and rejection of symlink evidence.

The normal repository gate remains:

```sh
make check
```

Because the existing CI workflow runs `make check` on every push and pull request, M6.7 is automatically exercised on GitHub-hosted runners.

## Relationship to AmiSandbox CI

AmiSandbox itself has a separate runtime qualification that builds the emulator with JIT disabled and boots using the built-in AROS fallback ROM. ASW M6.7 does not duplicate that build. Instead:

- **AmiSandbox CI** proves the emulator runtime/evidence producer;
- **ASW CI** proves the orchestration/evidence-consumer boundary;
- **physical N100 qualification** later proves the complete visible workstation path using the approved real ROM/OS corpus.

This separation keeps GitHub CI reproducible while retaining a stronger physical acceptance gate.

## Qualification state

Repository-side M6.7 is considered qualified only after the ASW GitHub Actions `CI` workflow passes with the M6.7 tests included. Physical end-to-end qualification remains pending until the N100 workstation performs a visible AmiSandbox run and ASW ingests the resulting evidence.
