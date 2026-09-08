# M4 Signature Candidate Pipeline

## Goal

M4 turns ASW analysis evidence into a reviewable, machine-readable signature candidate without turning analyst output directly into a verified AmiGuard detection.

The boundary is deliberate:

```text
sample evidence
  -> ASW candidate
  -> candidate validation
  -> AmiGuard research-format export
  -> clean-corpus qualification
  -> visible native AmiGuard qualification
  -> manual review
  -> separate promotion decision in AmiGuard
```

ASW never writes a candidate as `verified` or `infected` by itself.

## Candidate contract

A candidate records:

- stable candidate ID
- proposed name/family
- target kind: `file` or `bootblock`
- exact sample SHA-256
- evidence source references
- proposed signature representation
- qualification gate states
- analyst derivation note

Supported initial signature representations are:

1. `exact-sha256` — exact known sample identity.
2. `masked-pattern` — offset, byte pattern and byte mask; minimum eight bytes.
3. `structural` — references a separately implemented verifier rather than embedding sample bytes.

No live sample bytes are required in the candidate JSON.

## Gate semantics

Every candidate has three gates:

- `clean_corpus`
- `native_runtime`
- `manual_review`

Each is `pending`, `pass` or `fail`. Native runtime cannot be marked `pass` before clean-corpus qualification passes.

The exported AmiGuard JSON is always `status: research`, regardless of candidate gate state. Promotion remains an AmiGuard repository action after evidence review.

## Tooling

Validate:

```sh
python3 tools/asw_candidate.py validate candidate.json
```

Export an AmiGuard research proposal:

```sh
python3 tools/asw_candidate.py export-amiguard candidate.json --output proposal.json
```

The export shape follows AmiGuard's existing signature metadata conventions: schema, id, name, family, kind, status, source, provenance, sample SHA-256, signature/verifier, cleaner and research metadata.

## Evidence policy

Historical antivirus results, IRA/ADis output, HUNK inspection, SnoopDos/Scout observations and manual reverse engineering may all support a candidate. None is independently authoritative. Evidence references should identify the local evidence record, not copy proprietary signature databases or live malware into Git.

## Safety

- No candidate contains live malware bytes.
- No candidate is automatically promoted.
- `cleaner` exports as `none` in M4.
- Export always remains research-only.
- Hash mismatch between sample identity and an exact-hash signature is rejected.
- Symlink candidate inputs are rejected.

M5 performs the qualification gates needed before any real detection can be considered for integration.
