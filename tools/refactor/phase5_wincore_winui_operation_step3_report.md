# Phase 5 WinCore/WinUI Operation Boundary Step 3 Report

## Scope

- Make `WinUI` hold `VMOperations`.
- Do not replace existing `WinCore core` call sites.
- Do not migrate disk, tape, snapshot, or config calls.
- Do not change logic.
- Limit changes to compile-boundary preparation and report.

## Baseline

- Previous implementation commit:
  - `1160f16` `Add Win32 VM operation facade`
- User-side verification for `1160f16` passed:
  - VS2008 / VC8 Express `Release|Win32` build
  - writetag CRC `e7e35ae9`
  - M88 launch
  - D88 game launch
  - disk access
  - sound
  - snapshot save/load
  - clean shutdown
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes

`src/win32/ui.h`:

- included `vmops.h`
- added a `VMOperations* vmops` member

`src/win32/ui.cpp`:

- initialized `vmops` to `0` in `WinUI::WinUI`

## Why Pointer Holding

`VMOperations` currently contains a `WinCore` member.

Adding `VMOperations` by value to `WinUI` would construct a second unused `WinCore` instance. That would be more than a compile-boundary change, because `WinCore` construction/destruction can touch VM cleanup paths.

For this step, `WinUI` therefore holds only a pointer:

```text
VMOperations* vmops;
```

The pointer is not allocated and no call path uses it yet.

This keeps the step limited to a compile-visible ownership slot without changing runtime behavior.

## Intentionally Not Changed

- Existing `WinCore core` remains in `WinUI`.
- No `core.*` call sites were replaced.
- No `diskmgr->*` call sites were replaced.
- No `tapemgr->*` call sites were replaced.
- No snapshot save/load call sites were replaced.
- No config load/save/apply behavior was changed.
- No object lifetime was changed.
- No project files were changed in this step.

## Local Verification

Local checks:

```text
git diff --check
git diff -- src/win32/ui.cpp src/win32/ui.h
```

Results:

- `git diff --check` passed.
- Diff is limited to `src/win32/ui.h`, `src/win32/ui.cpp`, and this report.
- Local MSVC/VC8 build was not run because this WSL environment does not provide Visual Studio.

## User-Side Verification

User-side verification after commit `0ab7efc`:

```text
VS2008 / VC8 Express Release|Win32 build: passed
```

Runtime smoke:

- writetag CRC: appeared
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

If this builds and runs, the next implementation step should decide how to allocate and initialize `VMOperations` without replacing call sites.

Recommended next instruction:

```text
Phase 5 WinCore/WinUI operation boundary step 4 の設計だけ実行しろ。
WinUI が VMOperations をいつ生成/破棄するか、
既存 WinCore core と二重所有しない方法、
monitor 初期化、WinSound 取得、DiskManager/TapeManager lifetime への影響を report しろ。
実装はするな。
```

Do not migrate disk/tape/snapshot/config calls until `VMOperations` lifetime is settled.
