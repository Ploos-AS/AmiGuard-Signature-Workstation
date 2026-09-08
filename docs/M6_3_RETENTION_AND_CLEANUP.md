# M6.3 — Retention and safe cleanup

M6.3 separates evidence retention from disposable-analysis cleanup. The cleanup tool can remove only a specifically identified directory below the private ASW `work/` root. It has no code path for deleting immutable originals, manifests, queue records, audit logs, qualification evidence, ROMs or tool archives.

## Default policy

- **Immutable originals:** retain until an explicit separately reviewed legal/operational retention decision exists. M6.3 never deletes them.
- **Manifests, queue and audit records:** retain as operational evidence; M6.3 never deletes them.
- **Qualification/reverse-engineering evidence:** retain according to the case/evidence policy; M6.3 never automatically deletes it.
- **Disposable workspaces:** eligible only after the queue reaches terminal `closed` or `rejected` and the workspace marker has aged at least 7 days by default.

The seven-day value is a conservative default, not a claim about legal requirements.

## Workspace marker

Every disposable workspace intended for managed cleanup carries `.asw-disposable-workspace.json`:

```json
{
  "schema": 1,
  "sample_id": "asw-sample-id",
  "sample_sha256": "<64 lowercase hex>"
}
```

The matching M6.1 queue record must contain the same ID/SHA and be terminal. A mismatch fails closed.

## Dry-run / plan

```sh
python3 tools/asw_retention.py plan \
  --root /var/lib/asw \
  --sample-id asw-sample-id
```

`plan` never removes anything. It reports whether the exact workspace is eligible.

## Purge

```sh
python3 tools/asw_retention.py purge \
  --root /var/lib/asw \
  --sample-id asw-sample-id \
  --confirm-sha256 <exact-sample-sha256>
```

Purge requires an exact SHA-256 confirmation in addition to the sample ID. The tool refuses non-terminal cases, too-new workspaces, identity mismatch, top-level workspace symlinks and any symlink anywhere inside the workspace tree.

## Important limitations

Deletion means filesystem-level removal of a disposable workspace. It is **not** forensic secure erasure; SSD wear levelling, copy-on-write filesystems, snapshots and backups can retain prior blocks. Sensitive backup/snapshot handling is therefore an M6.4 concern.

The tool intentionally does not offer bulk wildcard cleanup. Operators clean one cryptographically identified sample workspace at a time and should append the cleanup decision/result to the M6.2 audit trail.
