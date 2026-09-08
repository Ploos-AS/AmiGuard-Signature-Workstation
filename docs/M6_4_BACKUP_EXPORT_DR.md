# M6.4 — Backup, export and disaster recovery

M6.4 defines how ASW operational state is backed up and restored without turning ordinary backups into an uncontrolled malware archive.

## Two backup classes

### Class A — operational metadata

Back up these by default:
- `manifests/`
- `queue/`
- `audit/`
- `evidence/`
- `candidates/`

These contain hashes, workflow state, analyst evidence and audit history, but must not contain live malware bytes.

### Class B — immutable originals

`originals/` contains hostile sample bytes. Backing it up is optional and must be a deliberate separate decision. If enabled, treat every copy, snapshot and off-site replica as malware storage with the same access-control, encryption and handling requirements as the ASW originals.

Disposable `work/`, `tmp/` and `exports/` are never part of the normal backup set.

## Backup manifest

`tools/asw_backup.py` creates a SHA-256 inventory of the protected tree. Originals are excluded unless `--include-originals` is explicitly supplied.

```sh
python3 tools/asw_backup.py create-manifest \
  --root /var/lib/asw \
  --output /secure/offline/asw-backup-manifest.json
```

For an intentionally malware-bearing backup:

```sh
python3 tools/asw_backup.py create-manifest \
  --root /var/lib/asw \
  --output /secure/offline/asw-full-manifest.json \
  --include-originals
```

The tool inventories and verifies; it does **not** create archives, transmit data, or provide encryption. Actual backup transport must use an independently authenticated encrypted mechanism chosen for the workstation environment.

## Encryption and storage policy

- Encrypt backup media at rest with a strong modern scheme.
- Keep decryption credentials outside the backup itself.
- Prefer at least one offline or physically disconnected copy for operational metadata.
- Do not mount malware-bearing backup media on unrelated systems.
- Do not sync originals to consumer cloud storage by accident.
- Treat hypervisor/filesystem snapshots containing originals as Class B malware storage.
- Record backup date, scope, manifest SHA-256 and the M6.2 audit-chain head in protected backup metadata.

## Audit checkpoint

Before backup, run:

```sh
python3 tools/asw_audit.py verify --log /var/lib/asw/audit/audit.jsonl
```

Record the resulting chain head next to the backup manifest in protected metadata. After restore, verify the audit chain again and compare its head with the recorded checkpoint.

## Restore qualification

A restore is not complete merely because files copied successfully. Verify the restored protected tree:

```sh
python3 tools/asw_backup.py verify \
  --root /restore/asw \
  --manifest /secure/offline/asw-backup-manifest.json
```

Then:
1. verify the M6.2 audit chain;
2. verify immutable original hashes against M1 manifests when originals were restored;
3. confirm permissions (`0400` originals, private operational state);
4. confirm no disposable analysis guest/workspace was restored as trusted state;
5. perform a harmless synthetic end-to-end ASW workflow before returning the workstation to production use.

## Disaster recovery order

1. Provision a clean ASW host from the M6.5 runbook.
2. Restore and verify Class A operational metadata.
3. Validate audit-chain checkpoint.
4. Restore Class B originals only if policy requires them, onto isolated ASW storage.
5. Verify each original by SHA-256/M1 manifest before analysis use.
6. Reinstall lawful local ROMs, Amiga OS media, historical antivirus and Aminet tools from separately verified sources rather than blindly restoring executable tooling.
7. Recreate disposable emulator bases/overlays from known-clean sources.
8. Run synthetic qualification and document the recovery event in the audit trail.

## Important limitation

A SHA-256 manifest detects unexpected content changes relative to that manifest. It does not prove that the backup medium is confidential, authentic, complete outside the listed scope, or safe to execute. Encryption, offline custody and independent checkpoint storage remain operational responsibilities.
