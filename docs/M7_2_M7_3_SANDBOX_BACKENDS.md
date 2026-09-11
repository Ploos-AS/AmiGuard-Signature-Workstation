# M7.2 / M7.3 — AtariSandbox and MacSandbox

## Decision

Create dedicated malware-analysis emulator forks rather than driving stock emulators only from wrapper scripts. Wrappers remain useful for orchestration, but the runtime must be able to emit stable machine-readable evidence from inside the emulator boundary, as AmiSandbox does for Amiga.

## AtariSandbox

### Base emulator

Use Hatari as the initial upstream candidate.

Reasons:

- mature ST/STE/TT/Falcon emulation
- built-in debugger and profiler
- tracing for CPU, OS calls and hardware events
- host control through FIFO/socket facilities
- snapshots and screenshots already exist
- EmuTOS provides a practical free CI boot path
- GPL-compatible fork model

### Initial scope

Start with ST/STE only. TT/Falcon are later profiles.

Initial profiles:

- Atari ST, 68000, TOS 1.00-class profile
- Atari ST, 68000, TOS 1.04-class profile
- Atari STE, 68000, TOS 1.62-class profile
- Atari ST/STE with current EmuTOS for CI

Exact proprietary TOS ROM bytes are local-only and identified by hashes.

### Required instrumentation

AtariSandbox should add a stable analysis mode with at least:

- `session.json`
- `events.jsonl`
- CPU register snapshots (D0-D7, A0-A7, PC, SR)
- exception/vector activity
- memory writes/watchpoints
- GEMDOS/BIOS/XBIOS calls
- process/program load/termination observations
- trap calls
- resident/vector modifications where observable
- floppy/HDD sector writes
- boot-sector modifications
- pre/post disk-image hashes
- screenshots
- deterministic machine/config fingerprint
- backend revision/build identity

Existing Hatari tracing/debugging should be reused internally where sensible, but ASW must not depend on parsing unstable human console text as its long-term evidence contract.

### Security defaults

- external networking disabled
- GEMDOS host-directory mounting disabled for malware sessions
- no writable host filesystem passthrough
- disposable writable disk images/overlays
- explicit disk-image based sample ingress
- JIT/dynarec-like acceleration disabled where relevant to deterministic tracing
- emulator IPC limited to the local analysis controller

## MacSandbox

### Base emulator

Use Basilisk II as the initial upstream candidate for 68k Macintosh analysis.

Reasons:

- explicitly targets 68k Macintosh
- supports Classic and Mac II style configurations
- open-source GPL codebase suitable for instrumentation
- Linux host support
- broader 68k Macintosh OS coverage than a narrowly model-specific emulator

Basilisk II requires a Macintosh ROM image and compatible System Software. These are not supplied by ASW/MacSandbox; exact local ROM/OS provenance and hashes must be recorded.

Mini vMac remains a useful secondary/reference emulator for early compact-Mac profiles, but is not the initial canonical backend because a single Basilisk II-derived backend gives a broader first matrix.

### Initial scope

Initial profiles should focus on classic 68k configurations rather than PowerPC:

- compact Mac / 68000-class reference profile where upstream capability permits
- Macintosh II-class 68020/68030 profile
- System 6/7 era analysis images as lawful local assets

The exact matrix must be qualified against what the chosen Basilisk II fork can reproduce reliably. Do not claim a model/CPU combination merely because the guest OS boots.

### Required instrumentation

MacSandbox analysis mode should expose at least:

- `session.json`
- `events.jsonl`
- 68k CPU register snapshots
- exception/vector activity
- memory writes/watchpoints
- trap/Toolbox call observations where practical
- process/application launch/termination observations
- INIT/system-extension loading observations
- resource-fork/file modifications
- disk block writes
- boot/system file changes
- pre/post disk-image hashes
- screenshots
- deterministic machine/config fingerprint
- backend revision/build identity

Classic Mac malware often interacts with System Folder contents, INITs/extensions, resource forks and filesystem metadata; those must be first-class evidence rather than reduced to ordinary byte-stream file hashes only.

### Security defaults

- networking disabled
- host shared folders disabled
- clipboard/host integration disabled where possible
- disposable writable disk images/overlays
- explicit image-based sample ingress
- no automatic host file import
- local-only IPC controller
- no signing/publication credentials in runtime

## Common runtime event envelope

Platform forks may have their own event payloads, but should converge on a common outer envelope:

```json
{
  "schema_version": 1,
  "platform": "atari-st | mac68k | amiga",
  "backend": "atarisandbox | macsandbox | amisandbox",
  "type": "...",
  "timestamp": "monotonic-or-deterministic-value",
  "payload": {}
}
```

ASW Core treats payloads as platform-specific unless a cross-platform event class is explicitly standardized.

## CI strategy

Atari is the easier next platform because Hatari + EmuTOS gives a fully redistributable GitHub Actions path similar in spirit to AmiSandbox + AROS.

Mac 68k CI must not assume redistribution rights for Apple ROM/System Software. Initial CI can still build MacSandbox and statically qualify the analysis-mode contract; real boot/runtime qualification should use lawfully supplied local assets until a clearly redistributable test path is identified.

## Recommended order

1. M7.1 extract the ASW Core contracts without breaking Amiga.
2. M7.2 create AtariSandbox first and qualify Hatari + EmuTOS in GitHub Actions.
3. Add Atari-specific downstream forensic interpretation.
4. M7.3 create MacSandbox from Basilisk II.
5. Qualify Mac runtime locally with hashed lawful ROM/System Software assets.
6. Only after benign qualification, introduce controlled hostile-sample workflows.
