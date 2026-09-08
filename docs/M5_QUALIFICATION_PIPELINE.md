# M5 — Qualification pipeline

M5 turns M4 candidates into evidence-backed, reviewable qualification records. It does **not** automatically promote signatures into AmiGuard.

## Gate order

1. `clean_corpus` — candidate must be tested against the known-clean corpus with zero false positives.
2. `native_runtime` — visible native AmiGuard test on the canonical A500/68000/Kickstart 1.2 profile. Headless emulator output is not sufficient for this gate.
3. `manual_review` — analyst reviews provenance, static/runtime evidence, historical AV observations and the proposed signature.

Each gate is `pending`, `pass` or `fail`. Native runtime cannot pass before clean corpus; manual review cannot pass before native runtime.

## Evidence record

Gate evidence is JSON with schema 1, exact candidate ID and sample SHA-256, a pass/fail result, and a non-empty evidence list. Evidence may refer to local ASW artifacts that cannot be committed publicly. Private sample bytes are never embedded.

Example:

```json
{
  "schema": 1,
  "gate": "clean_corpus",
  "candidate_id": "example.candidate",
  "sample_sha256": "<64 lowercase hex>",
  "result": "pass",
  "evidence": ["963 known-clean files scanned; zero candidate matches"]
}
```

Apply a gate:

```sh
python3 tools/asw_qualify.py candidate.json \
  --gate clean_corpus \
  --evidence clean-corpus-evidence.json \
  --output candidate-qualified.json
```

Always write to a new output path so earlier candidate/evidence state remains reviewable.

## Clean-corpus contract

The qualification runner may use AmiGuard's established known-clean corpus, but the corpus and exact scanner build must be identified in evidence. A candidate that matches any known-clean object fails. A pass is not proof that a signature is universally false-positive-free.

## Native runtime contract

The native gate is deliberately physical-ASW/manual. Required evidence records the AmiGuard commit/build, emulator profile, Kickstart/Workbench provenance locally, visible run, candidate sample identity, expected verdict and observed verdict. The canonical compatibility gate remains A500, Motorola 68000, Kickstart/Workbench 1.2, 512 KiB where applicable.

Runtime malware analysis can additionally use the M3 A500+/A1200 profiles and historical antivirus/reverse-engineering tools. Those observations do not replace the canonical AmiGuard compatibility gate.

## Promotion boundary

Even with all M5 gates passing, `asw_candidate.py export-amiguard` emits `status: research`. Moving a signature into AmiGuard's verified/active set remains an explicit AmiGuard repository review and integration action. No malware bytes cross that boundary.
