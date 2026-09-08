# M0 Safety and Trust Boundary

## Principle

ASW is an analyst workstation, not an extension of the public upload service. The public service accepts bytes; ASW handles explicitly selected, verified exports.

## Trust zones

1. **Public quarantine — untrusted storage**
   - owned by AmiGuard-Infrastructure
   - write-only from the public side
   - no execution, parsing, extraction, or public retrieval

2. **Transfer boundary — controlled crossing**
   - initiated manually by an administrator
   - exported with server-side metadata
   - sample SHA-256 and size verified before and after transfer
   - transfer media/path treated as hostile

3. **ASW immutable originals — evidence store**
   - original imported bytes preserved unchanged
   - no execution
   - read-only to normal analysis tooling after intake
   - identified by cryptographic digest rather than user filename

4. **ASW analysis workspace — disposable**
   - derived copies only
   - may be parsed, unpacked, inspected, or executed inside an isolated Amiga analysis environment when justified
   - host execution is forbidden
   - network disabled by default

5. **Signature output — reviewable clean data**
   - schemas, hashes, masks, offsets, structural constraints, verifier logic, notes, and qualification evidence
   - no live sample bytes
   - requires independent review and qualification before AmiGuard integration

## M0 invariants

- No automatic fetch from public quarantine.
- No live malware in Git.
- No host execution.
- No assumption that a submitted filename is trustworthy.
- No signature is promoted on name/reputation alone.
- Unknown/custom bootblocks are not automatically malware.
- EICAR or other synthetic fixtures remain test-signatures, never real detections.
- Analysis artifacts are not silently promoted to production signatures.

## Network policy

M0 requires only that the architecture support a network-disabled analysis path. Any future network-enabled analysis must be explicit, separately isolated, logged, and justified by a later milestone.

## Evidence

At minimum, each imported sample should eventually carry:

- ASW sample ID
- source submission ID when applicable
- SHA-256
- byte size
- import timestamp
- provenance note
- export verification result
- import verification result
- analyst status
- candidate signature references
- qualification references

M1 will define the machine-readable manifest.
