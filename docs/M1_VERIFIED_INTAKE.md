# M1 Verified Intake and Immutable Originals

## Goal

M1 defines the first executable crossing from a verified AmiGuard-Infrastructure export into ASW private storage without weakening either side's trust boundary.

## Import contract

An import requires all of the following from the operator:

- path to the explicitly exported sample
- source submission ID
- expected SHA-256
- expected byte size
- provenance note
- private ASW data root outside Git

The intake tool rejects symlinks and non-regular source files. It computes SHA-256 and size before committing any ASW record. A mismatch fails closed.

## Private layout

```text
ASW_DATA_ROOT/
  originals/
    sha256/
      ab/
        <full-sha256>.sample
  manifests/
    <full-sha256>.json
  tmp/
```

The digest is the ASW sample identity for M1. The submitted/original filename is deliberately not part of the identity or manifest.

## Commit semantics

1. Validate operator arguments.
2. Reject a symlink/non-regular source.
3. Compute source size and SHA-256.
4. Compare both with the expected export metadata.
5. Copy to a temporary file under the private data root while hashing again.
6. Verify copied size and SHA-256.
7. `fsync` the temporary sample.
8. Atomically install the original with no-overwrite semantics.
9. Set the original to read-only (`0400`).
10. Write a `0600` JSON manifest and `fsync` it before atomic install.
11. `fsync` containing directories.

If the same digest is imported again, M1 verifies that the existing original has the same hash and size and reports it as already present rather than overwriting it.

## Manifest fields

M1 records:

- `schema_version`
- `kind`
- `asw_sample_id`
- `sha256`
- `size`
- `source_submission_id`
- `imported_at`
- `provenance`
- `export_verified=true`
- `import_verified=true`
- `original_state=sealed-read-only`
- `executed_on_host=false`
- `analysis_status=new`

No submitted filename is retained.

## Safety invariants

- Public quarantine remains write-only to the Internet.
- ASW does not pull automatically from the VPS.
- Imported bytes never enter Git.
- Originals are never the analysis working copy.
- No host execution.
- No automatic archive extraction during import.
- Import success is not a malware classification.
- A historical antivirus verdict is evidence only.

## Qualification

CI uses harmless synthetic byte strings in temporary directories. A physical ASW qualification will later repeat the workflow using a harmless export fixture transferred through the real operator path. Live malware is unnecessary for qualifying M1 mechanics.
