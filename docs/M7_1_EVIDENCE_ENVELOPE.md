# M7.1 — ASW Core generic evidence envelope

M7.1 completes the next repository-side ASW Core extraction step by defining a small CPU-agnostic envelope around platform-specific evidence.

The envelope schema is `asw.core.evidence/1`. It binds evidence to an explicit platform/storage namespace, immutable sample SHA-256 and size, producer identity/revision, and one or more hash-bound evidence artifacts.

The Core envelope intentionally contains no CPU, chipset, operating-system, emulator, ROM or machine-model fields. Those details belong inside versioned platform/backend evidence. This prevents ASW Core from silently becoming an Amiga/m68k-specific API while still allowing the same custody layer to validate Amiga, Atari ST and Macintosh 68k evidence.

`analysis_started` is required to be `false`: this envelope is evidence/custody data and is never an authorization to execute a sample. Unknown platforms, namespace mismatches, malformed hashes/sizes, duplicate evidence roles and unexpected top-level fields fail closed.

Repository qualification is provided by `tests/test_evidence_envelope.py`, including the same contract for `amiga`, `atari-st` and `mac68k` and an explicit test proving a CPU-specific Core field is rejected.

This milestone does not activate planned platform backends and does not replace later visible physical qualification. Atari and Mac remain subject to their own backend/runtime gates.
