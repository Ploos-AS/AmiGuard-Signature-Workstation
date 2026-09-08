# M3 Isolated Amiga Runtime Lab

M3 defines the runtime-analysis environment for ASW. It is intentionally visible, disposable and network-disabled by default.

## Purpose

The lab has two complementary roles:

1. run historical Amiga antivirus programs against disposable copies to collect naming/family evidence;
2. run native Amiga analysis and reverse-engineering tools to inspect code, hunks, filesystem activity, tasks, residents and memory state.

Historical scanner verdicts and reverse-engineering observations are evidence. Neither automatically creates a production AmiGuard signature.

## Emulator matrix

The canonical initial profiles are stored in `config/emulator-profiles.json`:

- A500 / 68000 / Kickstart 1.2
- A500 / 68000 / Kickstart 1.3
- A500+ / 68000 / AmigaOS 2.04
- A1200 / 68020 / AmigaOS 3.1

All profiles require visible display output. Network is disabled by default. Guest state is disposable and must be restored from a known-clean base after every hostile-sample run.

## Historical antivirus suite

The initial reference set remains:

- VirusZ III
- VirusExecutor
- VirusChecker II
- VirusSlayer II
- Mill
- VT-Schutz

Exact binaries, hashes, provenance and licensing are local/private ASW data. They are never committed here.

## Native Amiga analysis toolbox

ASW should also maintain a curated, hashed toolbox of lawful Amiga utilities. The initial catalog includes Aminet tools useful for static inspection and runtime observation:

- **IRA 2.11** (`dev/asm/ira.lha`) — MC680x0 reassembler; primary disassembly/reassembly reference for OS 2.04+ profiles.
- **ADis 1.3** (`dev/asm/ADisV1_3.lha`) — older intelligent disassembler with source; useful as an independent comparison.
- **Disassem** (`dev/asm/Disassem.lha`) — simple 68000 disassembler for standard Amiga object files; useful for very early-format comparison.
- **Hunk 2.22** (`dev/misc/Hunk.lha`) — GUI hunk-structure editor/inspector for OS 2.x+.
- **HunkFunc 1.17** (`dev/moni/HunkFunc.lha`) — executable/link-object hunk structure viewer for OS 2.x+.
- **SnoopDos 3.11** (`util/moni/SnoopDos.lha`) — system/application monitor for DOS/library/device activity on OS 2.04+.
- **Scout 3.6** (`util/moni/Scout_os3.lha`) — system monitor for tasks, ports, residents, interrupts and related runtime state on OS 2.04+.
- **FileMaster 2.2** (`util/dir/FileMaster2.2.lha`) — runs on AmigaOS 1.2+ and provides hex/file/disk inspection, making it especially useful on the earliest lab profiles.

The toolbox catalog lives in `config/reference-tools.json`. Additional tools may be added only after recording source, exact archive/binary hashes, license/provenance and compatible guest profile.

## Runtime containment

For hostile samples:

- originals are never mounted writable in the guest;
- only disposable analysis copies enter the emulator;
- network is disabled unless a later, explicit exception is documented;
- shared folders, clipboard integration and host filesystem passthrough are disabled by default;
- base system disks are treated as immutable templates;
- writable guest overlays are destroyed after each run;
- screenshots/logs/verdict notes are exported as evidence, never guest malware binaries;
- no Amiga sample is executed directly by the Linux host.

## Evidence record

A runtime observation should record at minimum:

- ASW sample ID and SHA-256;
- emulator/profile ID;
- Kickstart/OS identity and hash where lawful to record;
- tool name/version and exact local binary SHA-256;
- clean-base image identity;
- start/end timestamp;
- network state;
- operator-visible verdict/observation;
- screenshots/log references when useful;
- whether guest state was destroyed after the run.

## Qualification boundary

M3 repository configuration can be CI-checked without proprietary ROMs or software. Actual M3 runtime qualification requires the physical ASW N100 workstation, lawful local ROM/OS/tool installations and visible emulator runs. CI cannot substitute for that gate.
