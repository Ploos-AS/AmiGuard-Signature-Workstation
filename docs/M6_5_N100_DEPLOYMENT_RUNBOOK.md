# M6.5 — N100 deployment runbook

This runbook defines the physical deployment and qualification contract for the AmiGuard Signature Workstation (ASW) on an Intel N100-class mini PC.

M6.5 does not claim that the physical workstation has been provisioned. Repository-side work is complete only when this runbook and its machine-readable checklist are in CI; physical qualification remains a separate operator task.

## 1. Host baseline

Target:

- dedicated Intel N100-class mini PC
- x86-64 Linux host
- UEFI Secure Boot enabled where practical
- virtualization enabled in firmware
- full-disk encryption where practical
- dedicated ASW use; no unrelated personal data or production secrets
- local analyst account with sudo only when needed
- host firewall default-deny inbound
- automatic security updates enabled
- system clock synchronized

Recommended initial host OS: Ubuntu 24.04 LTS or Debian 13. The exact distribution is less important than reproducibility, long-term support, and availability of AmiSandbox and the required analysis tooling.

## 2. Storage layout

Keep Git checkouts separate from private ASW data.

Suggested layout:

```text
/opt/asw/repo/                    ASW Git checkout
/opt/asw/amisandbox/              AmiSandbox Git checkout/build
/var/lib/asw/
  originals/sha256/               immutable imported originals
  manifests/                      intake manifests
  queue/                          M6.1 analyst queue
  audit/audit.jsonl               M6.2 audit trail
  evidence/                       analyst/runtime evidence
  candidates/                     local candidate working data
  work/                           disposable per-sample workspaces
  tmp/                            temporary files
  exports/                        controlled outbound review bundles
  backups/                        local staging only; not the only backup copy
```

Private data directories should be owned by the dedicated analyst account and not be readable by unrelated users.

## 3. Network model

The ASW host may use the network for OS/package updates and ordinary Git operations when no sample runtime is active.

The AmiSandbox analysis runtime is different:

- guest/emulator network is disabled by default
- no automatic fetch from `amiguard.ploos.no`
- no direct mount of public quarantine storage
- no automatic cloud upload of samples/evidence
- no shared clipboard or broad shared folders
- no host filesystem passthrough except explicit disposable transfer media/workspace needed for the run

If a future analysis requires network access, it must be an explicit documented exception with a dedicated evidence record.

## 4. AmiSandbox runtime stack

Install and build **AmiSandbox (`Ploos-AS/AmiSandbox`) as the canonical ASW dynamic-analysis emulator**. Generic FS-UAE/Amiberry may remain useful for comparison or unrelated compatibility work, but they do not substitute for AmiSandbox when ASW claims dynamic malware-analysis evidence.

Use an analysis-oriented AmiSandbox build with JIT disabled. Record the exact Git revision/build identity used for qualification.

Required profiles:

1. A500 / 68000 / Kickstart 1.2 / AmigaOS 1.x
2. A500 / 68000 / Kickstart 1.3 / AmigaOS 1.x
3. A500+ equivalent / 68000 / Kickstart 2.04 / AmigaOS 2.04
4. A1200 / 68020 / Kickstart 3.0 / AmigaOS 3.0
5. A1200 / 68020 / Kickstart 3.1 / AmigaOS 3.1

All runtime profiles must remain visible for qualification work, use disposable writable state, disable guest networking by default, disable JIT for analysis, and disable broad host filesystem sharing by default.

AmiSandbox analysis sessions must produce at least `session.json` and `events.jsonl`; these are copied into the ASW evidence store and hashed. Additional AmiSandbox artifacts are retained when relevant.

The canonical AmiGuard native qualification gate remains A500 / 68000 / Kickstart/Workbench 1.2. Headless-only output is not sufficient for that gate.

## 5. ROM and Workbench provenance

ROMs, Workbench disks and other copyrighted system software must be acquired lawfully and remain local.

For every local system image used as qualification evidence record:

- source/provenance
- descriptive version
- SHA-256
- local path or inventory identifier
- date verified

Do not commit ROMs or Workbench disk images to Git.

## 6. Historical antivirus reference suite

Install only lawfully acquired local copies of the historical reference tools cataloged by ASW:

- VirusZ III
- VirusExecutor
- VirusChecker II
- VirusSlayer II
- Mill
- VT-Schutz

For each binary/database record exact local SHA-256, version, provenance and license/redistribution status.

Historical antivirus verdicts are evidence only. They never automatically name or promote an AmiGuard signature.

## 7. Native Amiga analysis toolbox

Install and provenance-record the Aminet/native tools cataloged by M3, including as appropriate:

- IRA
- ADis
- Disassem
- Hunk
- HunkFunc
- SnoopDos
- Scout
- FileMaster 2.2

Archive SHA-256 and installed binary SHA-256 should be recorded independently. Public ASW Git contains metadata/recipes only, not downloaded tool archives unless redistribution rights are explicit.

## 8. Sample transfer and intake

Samples arrive only through explicit admin export from the public quarantine.

Before analysis:

1. Export the selected submission manually.
2. Record submission ID, expected size and SHA-256.
3. Transfer using controlled media/path treated as hostile content.
4. Run `tools/asw_intake.py import`.
5. Verify the sealed original and manifest.
6. Create an M6.1 queue record.
7. Append an M6.2 audit event for import/acceptance.

Never analyse the immutable original directly. Create a disposable analysis copy under `work/<sample-id>/`.

## 9. Runtime discipline

Before each visible AmiSandbox run:

- verify sample SHA-256
- verify AmiSandbox revision/build identity
- verify selected ASW/AmiSandbox profile mapping
- verify clean base disk identity
- verify JIT disabled
- verify network disabled
- verify original is not mounted writable
- start from a clean/disposable overlay
- allocate a fresh `AMISANDBOX_ANALYSIS_DIR`

During the run capture the visible result and relevant observations.

After the run:

- preserve and hash `session.json` and `events.jsonl`
- export intended AmiSandbox screenshots/logs/dumps/other artifacts as evidence
- record tool name/version/binary SHA-256 and guest profile where applicable
- record sample SHA-256 and timestamps
- record whether guest writable state was destroyed
- destroy disposable guest state when no longer needed
- keep originals untouched

## 10. Qualification sequence

For a real candidate, the ordered qualification contract remains:

1. static/reverse-engineering evidence sufficient to justify the candidate
2. AmiSandbox dynamic evidence where applicable
3. clean-corpus qualification with zero known-clean matches
4. visible native AmiGuard run on canonical A500/68000/Kickstart 1.2
5. manual analyst review
6. research-only export from ASW
7. separate explicit promotion decision in the AmiGuard repository

ASW does not directly mark a signature as production `verified` or `infected`.

## 11. Backup and audit

Before and after significant workstation changes:

- verify the M6.2 audit chain
- record the current audit head externally
- create an M6.4 operational backup
- encrypt backup media/storage
- keep at least one offline copy
- treat any backup containing `originals/` as malware storage
- perform restore tests periodically

## 12. Physical acceptance checklist

The physical workstation is accepted only after all of the following are manually verified and recorded:

- dedicated N100 host installed and patched
- disk encryption decision recorded
- virtualization available
- inbound firewall default deny
- private ASW data root permissions verified
- repository `make check` PASS on the N100
- AmiSandbox cloned/built from a recorded revision
- AmiSandbox analysis-oriented build has JIT disabled
- all five canonical AmiSandbox profiles created and visible
- guest networking disabled by default
- shared folders/host passthrough disabled by default
- lawful ROM/Workbench inventory created with SHA-256
- historical antivirus inventory created with SHA-256/provenance
- Aminet/native analysis-tool inventory created with SHA-256/provenance
- harmless synthetic intake fixture PASS
- queue/audit lifecycle PASS
- harmless AmiSandbox analysis session produces valid `session.json` and `events.jsonl`
- AmiSandbox artifacts copied to ASW evidence and SHA-256 verified
- backup creation + verification PASS
- restore rehearsal PASS
- visible A500/68000/Kickstart 1.2 harmless runtime smoke PASS

A real malware sample is not required to accept the workstation itself.

## 13. Completion boundary

M6.5 repository-side completion means the deployment contract is versioned and CI-checked. Physical ASW qualification is complete only when the above acceptance evidence exists from the actual N100 workstation using the canonical AmiSandbox runtime defined by M6.6.
