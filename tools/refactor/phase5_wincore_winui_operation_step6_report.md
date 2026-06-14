# Phase 5 WinCore/WinUI Operation Boundary Step 6 Report

## Scope

- Allocate `VMOperations` in `WinUI::InitM88`.
- Bind it to the existing `WinCore core`, `DiskManager`, and `TapeManager`.
- Unbind and delete it in `WinUI::CleanupM88`.
- Do not replace existing `core`, `diskmgr`, or `tapemgr` call sites.
- Do not migrate disk, tape, snapshot, or config call sites.
- Do not change VM logic.

## Baseline

- Previous implementation commit:
  - `7db9faa` `Make VM operations reference WinCore`
- Step 5 user-side verification passed:
  - VS2008 / VC8 Express `Release|Win32` build
  - writetag CRC appeared
  - M88 launch
  - D88 game launch
  - disk access
  - sound
  - snapshot save/load
  - clean shutdown
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes

`src/win32/ui.cpp`:

- `WinUI::InitM88`
  - allocates `VMOperations` if `vmops` is null
  - returns `false` if allocation fails
  - calls `vmops->Bind(&core, diskmgr, tapemgr)` after `core.Init` succeeds

- `WinUI::CleanupM88`
  - calls `vmops->Unbind()`
  - deletes `vmops`
  - sets `vmops` to `0`
  - does this before `core.Cleanup()` and before deleting `diskmgr` / `tapemgr`

## Why This Ordering

Allocation occurs after `diskmgr` and `tapemgr` exist.

Binding occurs after `core.Init` succeeds, so `VMOperations` references the initialized active `WinCore`.

Unbind/delete occurs before:

```text
core.Cleanup();
delete diskmgr;
delete tapemgr;
```

This prevents `VMOperations` from retaining pointers to objects that are being cleaned up or deleted.

## Intentionally Not Changed

- Existing `WinCore core` remains owned by `WinUI`.
- Existing `core.*` call sites are unchanged.
- Existing `diskmgr->*` call sites are unchanged.
- Existing `tapemgr->*` call sites are unchanged.
- Snapshot save/load call sites are unchanged.
- Config load/save/apply call sites are unchanged.
- Monitor initialization remains direct to `core`.
- `core.GetSound()` call sites remain direct.
- Project files are unchanged.

## Local Verification

Local checks:

```text
git diff --check
git diff -- src/win32/ui.cpp
```

Results:

- `git diff --check` passed.
- Source diff is limited to `WinUI::InitM88` and `WinUI::CleanupM88`.
- Local MSVC/VC8 build was not run because this WSL environment does not provide Visual Studio.

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

If this builds and runs, the next step should be a very small call migration.

Recommended first migration:

```text
Phase 5 WinCore/WinUI operation boundary step 7 を小さく実行しろ。
WinUI の低リスクな core.GetExecCount() 1 箇所だけを vmops->GetExecCount() に置換しろ。
disk/tape/snapshot/config 呼び出し元変更は禁止。
WinCore/DiskManager/TapeManager 実装変更は禁止。
完了後 report を出せ。
```

This avoids disk/tape/snapshot/config behavior while proving one read-only VM operation route.
