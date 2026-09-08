# M1 Historical Antivirus Reference Suite

## Why ASW needs it

Old Amiga malware is often better documented by contemporary antivirus programs than by modern generic tooling. Running several historical scanners against a disposable copy can provide names, aliases, bootblock classifications and family clues that guide manual signature research.

This is a **reference-identification lab**, not a source of truth and not a signature-database harvesting project.

## Initial tool inventory

The initial inventory, based on the supplied Amiga antivirus reference, is:

| Tool | Reference version | Compatibility noted in reference | ASW role |
| --- | --- | --- | --- |
| VirusZ III | v1.04fs | AmigaOS 2.0+, 3.0+, 4+, AROS, MorphOS | broad historical comparison |
| VirusExecutor | v2.34 | AmigaOS 2.0+, 3.0+ | historical naming/comparison |
| VirusChecker II | v2.5 | AmigaOS 2.0+, 3.0+ | historical naming/comparison |
| VirusSlayer II | v1.0b | AmigaOS 2.0+, 3.0+ | historical naming/comparison |
| Mill | v0.85 | AmigaOS 2.0+, 3.0+ | historical naming/comparison |
| VT-Schutz | v3.17 | AmigaOS 1.2+, 1.3+ | crucial early-Kickstart comparison |

Versions are reference targets, not proof that a specific downloadable binary is authentic. Every locally installed binary must be acquired lawfully, provenance-recorded and hashed before use.

## Planned emulator matrix

M3 should instantiate at least these visible, disposable profiles:

1. **A500 / 68000 / Kickstart 1.2** — early baseline; VT-Schutz-compatible path and AmiGuard minimum target.
2. **A500 / 68000 / Kickstart 1.3** — common early-virus environment.
3. **A500+ or equivalent / 68000 / AmigaOS 2.x** — historical AV tools requiring 2.0+.
4. **A1200 / 68020 / AmigaOS 3.x** — later historical scanners and broader compatibility.

Additional profiles can be added when a tool or sample requires them, but the matrix should stay reproducible and small.

## Runtime rules

- Visible emulator runs are required when verdicts are used as qualification evidence.
- Network is disabled by default.
- Samples enter only as disposable analysis copies.
- Reference system disks should be restored from a known clean snapshot after each run.
- Original ASW evidence bytes are never mounted writable in the guest.
- Clipboard/shared-folder conveniences should be disabled unless a controlled transfer mechanism requires them.
- Results should record tool name, exact binary SHA-256, version, guest profile, sample SHA-256, timestamp and displayed verdict.

## Interpretation policy

A historical program saying `Virus X` does **not** prove the sample is Virus X. Useful confidence comes from agreement between several independent observations, such as:

- multiple historical scanners agree on family/name
- bootblock/file structure matches documented behavior
- stable byte pattern or structural verifier exists
- clean corpus does not collide
- manual reverse engineering supports the conclusion
- visible native AmiGuard qualification succeeds

Conflicting names must be preserved as aliases/evidence rather than silently normalized.

## Legal and repository boundary

The reference programs and their signature databases may have licenses that do not permit redistribution. Therefore:

- binaries/databases are kept only in the private ASW lab unless redistribution rights are clear
- this public repository stores only catalog metadata, hashes, configuration recipes and evidence that is safe to publish
- ASW does not extract or copy proprietary signature databases into AmiGuard

The objective is independent analysis and independently authored AmiGuard signatures.
