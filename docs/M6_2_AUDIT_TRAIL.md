# M6.2 — Append-only audit trail

M6.2 adds a local JSONL audit trail for analyst actions. Each event is hash-chained to the previous event, providing tamper evidence for modification, deletion/reordering inside the retained chain, and accidental corruption.

This is **tamper-evident, not tamper-proof**. An attacker able to replace the complete log and every external checkpoint can construct a new chain. M6.4 therefore includes backup/checkpoint policy.

## Event fields

Each event contains schema version, monotonically increasing sequence, UTC timestamp, ASW sample ID, exact sample SHA-256, analyst identity, action, optional note, previous event hash, and SHA-256 of the canonical event body.

No malware bytes, submitter identity, original submitted filename, credentials, ROMs or proprietary tool binaries belong in the audit log.

## Usage

```sh
python3 tools/asw_audit.py append \
  --log /var/lib/asw/audit/audit.jsonl \
  --sample-id asw-123 \
  --sha256 <64-lowercase-hex> \
  --actor pgo \
  --action static-analysis-started

python3 tools/asw_audit.py verify --log /var/lib/asw/audit/audit.jsonl
```

Before every append, the existing chain is fully verified. Append uses `O_APPEND`, mode 0600, flush and fsync. Symlink logs are rejected. The tool never edits an earlier event.

## Operational contract

- Keep audit storage outside the public Git checkout.
- Restrict it to the ASW analyst account.
- Run `verify` before backup/export and after restore.
- Record the current chain head in protected backup metadata/checkpoints.
- Queue state and audit trail are complementary: M6.1 coordinates work; M6.2 records operator actions.
- Do not treat an audit event as evidence that a qualification gate passed; M5 evidence remains authoritative for qualification.
