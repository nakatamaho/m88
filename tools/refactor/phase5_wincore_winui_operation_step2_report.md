# Phase 5 WinCore/WinUI Operation Boundary Step 2 Report

## Scope

- Add `VMOperations` under `src/win32`.
- Implement only thin wrappers around existing `WinCore`, `DiskManager`, and `TapeManager`.
- Do not change `WinUI` call sites.
- Do not change `WinCore` public API.
- Do not change `DiskManager` / `TapeManager` implementation.
- Do not change snapshot/config logic.
- Add only necessary project file references.

## Baseline

- Pushed commit:
  - `c2836cb` `Design WinCore WinUI operation facade`
- Previous user-side VC2008 / VC8 Express verification before this step passed:
  - `Release|Win32` rebuild
  - writetag CRC
  - launch
  - D88 game
  - disk access
  - sound
  - snapshot save/load
  - clean shutdown
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Files Added

```text
src/win32/vmops.h
src/win32/vmops.cpp
tools/refactor/phase5_wincore_winui_operation_step2_report.md
```

## Project References Added

```text
M88_2008.vcproj: src\win32\vmops.cpp
M88_2008.vcproj: src\win32\vmops.h
M88.dsp:         .\src\win32\vmops.cpp
M88.dsp:         .\src\win32\vmops.h
```

## Implementation Summary

Added `VMOperations` as a Win32-side facade.

It owns:

```text
WinCore core
DiskManager* diskmgr
TapeManager* tapemgr
```

The wrapper currently delegates to existing objects only.

`WinCore` wrappers:

```text
Init
Cleanup
Start
Stop
Reset
ApplyConfig
SaveSnapshot
LoadSnapshot
GetSound
GetExecCount
Lock
Unlock
QueryIF
```

`DiskManager` wrappers:

```text
MountDisk
UnmountDisk
GetNumDisks
GetCurrentDisk
GetDiskTitle
IsDiskImageOpen
AddDisk
FormatDisk
```

`TapeManager` wrappers:

```text
OpenTape
CloseTape
IsTapeOpen
```

## Intentionally Not Changed

- No `WinUI` call sites changed.
- No `WinCore` public API changed.
- No `DiskManager` behavior changed.
- No `TapeManager` behavior changed.
- No snapshot file format or load/save behavior changed.
- No config load/save/apply behavior changed.
- No display/input/sound behavior changed.
- No SDL2 code added.

## Deferred On Purpose

These were not added in this step because they are not direct thin wrappers yet:

- `SelectDisk`
  - Current `WinUI::SelectDisk` depends on `WinUI::DiskInfo` state:
    - filename
    - readonly flag
    - menu check state
    - current disk id
  - Moving this requires a later UI call migration step.

- `GetConfig`
  - `WinCore::config` is private.
  - `WinUI` currently owns the active `PC8801::Config`.
  - Exposing config ownership should be a separate config-boundary decision.

## Verification

Local checks:

```text
git diff --check
rg -n "vmops" M88_2008.vcproj M88.dsp src/win32/vmops.h src/win32/vmops.cpp
```

Results:

- `git diff --check` passed.
- `vmops.cpp` and `vmops.h` are referenced by both `M88_2008.vcproj` and `M88.dsp`.
- Local MSVC/VC8 build was not run because this WSL environment does not provide Visual Studio.

## User-Side Verification

User-side verification after commit `1160f16`:

```text
VS2008 / VC8 Express Release|Win32 build: passed
M88 build result: errors 0, warnings 6
writetag CRC: e7e35ae9
```

Runtime smoke:

- M88 launch: passed
- D88 game launch: passed
- disk access: passed
- sound: passed
- snapshot save/load: passed
- clean shutdown: passed
- new warning/dialog/crash: none

## User-Side Verification Request

Recommended:

```text
tools\windows\build_vc2008.cmd Release
```

Then verify:

- writetag CRC appears
- M88 launch
- D88 game launch
- disk access
- sound
- snapshot save/load
- clean shutdown
- no new warning dialog or crash

## Next Safe Step

If this builds and runs, the next step should migrate one low-risk read-only call from `WinUI` to `VMOperations`.

Recommended next instruction:

```text
Phase 5 WinCore/WinUI operation boundary step 3 を小さく実行しろ。
WinUI に VMOperations を追加するが、まずは既存 WinCore core を置き換えず、
disk/tape/snapshot/config の呼び出し元変更は禁止。
コンパイル可能な保持だけを確認し、必要な最小 include/project 変更と report のみに限定しろ。
```

An even safer alternative is another design step for how `WinUI` should hold `VMOperations` without disrupting monitor initialization.
