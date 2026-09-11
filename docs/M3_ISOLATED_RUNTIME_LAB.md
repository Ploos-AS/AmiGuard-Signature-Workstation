# M3 Isolated Amiga Runtime Lab

M3 defines the runtime-analysis environment for ASW. It is intentionally visible, disposable and network-disabled by default.

## Purpose

The lab has three complementary roles:

1. execute hostile or suspicious Amiga artifacts under AmiSandbox and collect machine-readable dynamic evidence;
2. run historical Amiga antivirus programs against disposable copies to collect naming/family evidence;
3. run native Amiga analysis and reverse-engineering tools to inspect code, hunks, filesystem activity, tasks, residents and memory state.

Historical scanner verdicts and reverse-engineering observations are evidence. Neither automatically creates a production AmiGuard signature.

## Canonical runtime backend

**AmiSandbox (`Ploos-AS/AmiSandbox`) is the canonical dynamic-analysis emulator for ASW.** Generic FS-UAE/Amiberry installations are not substitutes when ASW claims dynamic-analysis evidence.

ASW invokes AmiSandbox in its opt-in analysis mode and records the exact AmiSandbox revision/build identity used for every evidentiary run. At minimum, each completed AmiSandbox session must preserve `session.json` and `events.jsonl`. As AmiSandbox gains additional event classes, ASW may ingest CPU/register snapshots, memory-write traces, vector/exception activity, Exec/process/library/device activity, disk and bootblock events, hashes, snapshots, screenshots and explicitly enabled network evidence.

AmiSandbox remains a defense-in-depth component, not the sole security boundary. Host containment and ASW sample-handling rules still apply.

## Emulator matrix

The canonical profiles are stored in `config/emulator-profiles.json` and mapped to AmiSandbox profiles:

- A500 / 68000 / Kickstart 1.2
- A500 / 68000 / Kickstart 1.3
- A500+ / 68000 / AmigaOS 2.04
- A1200 / 68020 / AmigaOS 3.0
- A1200 / 68020 / AmigaOS 3.1

All profiles require visible display output for qualification work. Analysis mode uses JIT disabled, network disabled by default, disposable writable state and no broad host filesystem passthrough or shared folders.

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
- only disposable analysis copies enter AmiSandbox;
- AmiSandbox analysis mode is mandatory for dynamic-evidence runs;
- JIT is disabled for analysis-oriented builds/runs;
- network is disabled unless an explicit exception is documented;
- shared folders, clipboard integration and host filesystem passthrough are disabled by default;
- base system disks are treated as immutable templates;
- writable guest overlays are destroyed after each run;
- intended AmiSandbox artifacts are exported into the ASW evidence store;
- no Amiga sample is executed directly by the Linux host.

## Evidence record

A runtime observation should record at minimum:

- ASW sample ID and SHA-256;
- AmiSandbox Git revision/build identity;
- ASW profile ID and AmiSandbox profile ID;
- Kickstart/OS identity and hash where lawful to record;
- tool name/version and exact local binary SHA-256 when a guest tool is used;
- clean-base image identity;
- start/end timestamp;
- network state;
- JIT state;
- `session.json` reference and SHA-256;
- `events.jsonl` reference and SHA-256;
- operator-visible verdict/observation;
- screenshots/log references when useful;
- whether guest state was destroyed after the run.

## ASW pipeline boundary

The intended dynamic path is:

```text
AmiGuard submission/quarantine
        -> verified ASW intake
        -> immutable original + disposable copy
        -> AmiSandbox analysis session
        -> session.json + events.jsonl + artifacts
        -> AmiForensics / analyst interpretation
        -> signature candidate
        -> clean-corpus + native AmiGuard qualification
        -> manual review
        -> research-only export
```

AmiSandbox produces evidence; it does not approve or publish signatures. ASW owns orchestration, evidence association, candidate generation/qualification and review state.

## Qualification boundary

M3 repository configuration can be CI-checked without proprietary ROMs or software. Actual runtime qualification requires the physical ASW N100 workstation, a qualified AmiSandbox build, lawful local ROM/OS/tool installations and visible emulator runs. CI cannot substitute for that gate.
