# M4 Signature Candidate Pipeline

## Goal

M4 turns ASW analysis evidence into a reviewable, machine-readable signature candidate without turning analyst output directly into a verified detection.

ASW now treats the candidate as the **canonical signature source**. Consumer-specific formats are deterministic exports from that candidate:

```text
sample evidence
  -> ASW candidate
  -> candidate validation
  -> clean-corpus/native/manual qualification
  -> consumer exporters
       -> AmiGuard research JSON
       -> AAA Signature Factory candidate JSON
       -> optional ClamAV local signature (.hsb/.ndb)
  -> consumer-side validation/promotion
```

ASW never writes a candidate as `verified`, `infected` or production-promoted by itself.

## Candidate contract

A candidate records:

- stable candidate ID
- proposed name/family
- target kind: `file` or `bootblock`
- exact sample SHA-256
- optional exact bootblock SHA-256
- optional sample size and format
- optional deterministic `created_at` provenance timestamp
- evidence source references
- proposed signature representation
- qualification gate states
- analyst derivation note

Supported initial signature representations are:

1. `exact-sha256` — exact known object identity.
2. `masked-pattern` — offset, byte pattern and byte mask; minimum eight bytes.
3. `structural` — references a separately implemented verifier rather than embedding sample bytes.

No live sample bytes are required in the candidate JSON.

## Gate semantics

Every candidate has three gates:

- `clean_corpus`
- `native_runtime`
- `manual_review`

Each is `pending`, `pass` or `fail`. Native runtime cannot be marked `pass` before clean-corpus qualification passes.

Consumer export does not bypass these gates. AmiGuard output remains research-only. AAA output remains a `candidate`, never `promoted`. ClamAV output is a local signature artifact only and must be corpus-tested before distribution.

## Tooling

Validate:

```sh
python3 tools/asw_candidate.py validate candidate.json
```

Export an AmiGuard research proposal:

```sh
python3 tools/asw_candidate.py export-amiguard candidate.json --output proposal.json
```

Export an AAA Signature Factory candidate:

```sh
python3 tools/asw_candidate.py export-aaa candidate.json --output aaa-candidate.json
```

AAA export follows the native `Ploos-AS/Amiga-Antivirus-Appliance` M7 candidate schema. Exact file SHA-256, exact bootblock SHA-256 and fixed byte patterns are supported where the ASW representation can be mapped losslessly. Masked patterns with non-`ff` mask bytes and structural verifiers remain ASW-only until AAA has an equivalent native representation.

Export a ClamAV local signature:

```sh
python3 tools/asw_candidate.py export-clamav candidate.json --output candidate.hsb
python3 tools/asw_candidate.py export-clamav candidate.json --output candidate.ndb
```

ClamAV export is intentionally conservative:

- an exact full-file SHA-256 becomes a `.hsb` line and requires `sample_size`;
- a masked fixed-offset pattern becomes an `.ndb` extended signature only when every mask byte can be represented exactly as ClamAV content syntax (`ff`, `00`, `f0`, `0f`);
- bootblock-only hashes are not exported as full-file ClamAV hashes;
- structural verifier candidates are not translated automatically.

The generated files are intended for local qualification with `clamscan -d <signature-file>`. ASW does not create Cisco/Talos-signed CVD packages or claim inclusion in the official ClamAV database.

## AmiGuard output

The AmiGuard export shape follows AmiGuard signature metadata conventions: schema, id, name, family, kind, status, source, provenance, sample SHA-256, signature/verifier, cleaner and research metadata.

The exported AmiGuard JSON is always `status: research` regardless of candidate gate state. Promotion remains an AmiGuard repository action after evidence review.

## AAA output

AAA already contains an M7 Signature Factory, corpus qualification, ClamAV integration and signed/versioned signature distribution. ASW therefore exports into AAA's native candidate boundary rather than replacing AAA's promotion/distribution machinery.

For deterministic AAA provenance, new ASW candidates intended for AAA export should include `created_at`. `aaa_confidence` may be explicitly set to `single-engine`, `corroborated` or `confirmed`; without it ASW stays conservative and uses `single-engine` until all three ASW qualification gates pass, at which point it may export `confirmed`.

## Evidence policy

Historical antivirus results, IRA/ADis output, HUNK inspection, SnoopDos/Scout observations, AmiSandbox evidence, AmiForensics output and manual reverse engineering may all support a candidate. None is independently authoritative. Evidence references should identify the local evidence record, not copy proprietary signature databases or live malware into Git.

## Safety

- No candidate contains live malware bytes.
- No candidate is automatically promoted.
- `cleaner` exports as `none` for AmiGuard research output.
- AmiGuard export always remains research-only.
- AAA export always remains candidate-state.
- ClamAV export is a local qualification artifact, not an official database publication.
- Hash mismatch between sample identity and an exact file signature is rejected.
- Symlink candidate inputs are rejected.
- Lossy signature translations are rejected rather than guessed.

M5 performs the qualification gates needed before any real detection can be considered for integration or distribution.
