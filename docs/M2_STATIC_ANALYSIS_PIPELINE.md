# M2 Static Analysis Pipeline

M2 adds deterministic, host-safe static analysis for imported ASW samples. The pipeline works only on analysis copies or immutable originals as read-only input; it never executes the sample and never modifies source bytes.

## Scope

The first static evidence bundle records:

- sample identity and SHA-256
- byte size
- coarse file-kind classification
- Amiga bootblock facts for inputs at least 1024 bytes long
- HUNK header facts for likely Amiga executables
- printable-string excerpts with bounded output
- deterministic JSON evidence

M2 intentionally does not identify malware by product name. Historical antivirus tools are reference evidence and belong to the later isolated-emulation milestone. A match reported by VirusZ, VirusExecutor, VirusChecker II, VirusSlayer II, Mill, VT-Schutz, or another legacy scanner must not be promoted automatically to an AmiGuard signature.

## Bootblock evidence

For the first 1024 bytes M2 records:

- DOS-family marker when present (`DOS` + flags byte)
- raw bootblock SHA-256
- Amiga bootblock checksum validity using the standard end-around-carry sum
- first longwords in big-endian hexadecimal form

A valid checksum is structural evidence only. It does not mean a bootblock is clean. An unknown/custom bootblock is not automatically infected.

## HUNK evidence

M2 recognizes the big-endian `HUNK_HEADER` magic `0x000003F3` at offset zero and records bounded header-table facts when parseable. It does not execute relocation logic, load segments, or emulate code.

Malformed or truncated input must result in explicit bounded evidence rather than a crash.

## Evidence bundle

`tools/asw_static.py` writes a JSON object with `schema_version: 1` and deterministic key ordering. No source filename is needed for identity. The command can print to stdout or write to an explicitly chosen output path outside the public repository.

Example:

```sh
python3 tools/asw_static.py /srv/asw/originals/<id>/sample --output /srv/asw/evidence/<id>/static.json
```

The evidence file itself contains no live sample bytes.

## Qualification gate

M2 is complete when:

1. repository tests cover bootblock checksum, truncated input, HUNK recognition, generic file evidence, and deterministic JSON;
2. `make check` passes;
3. exact-HEAD CI passes.

No native Amiga runtime qualification is required for M2 because the new code is host-side read-only analysis tooling. Native qualification remains required later before any candidate becomes a verified AmiGuard detection.
