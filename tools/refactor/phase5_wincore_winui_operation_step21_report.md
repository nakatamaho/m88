# Phase 5 WinCore/WinUI Operation Boundary Step 21 Report

## Scope

- Route only `WinUI::SaveSnapshot()` through `VMOperations`.
- Preserve fallback to the existing direct `core.SaveShapshot(name)` call.
- Do not change `WinUI::LoadSnapshot()`.
- Do not change snapshot name generation, status messages, `currentsnapshot`,
  or `snapshotchanged`.
- Do not change `WinCore`, `VMOperations`, disk, tape, sound, lifecycle, or
  monitor implementation.

## Baseline

- Previous pushed commit:
  - `e0bb219` `Inventory remaining WinUI operation boundaries`
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Change

`src/win32/ui.cpp`, inside `WinUI::SaveSnapshot()`:

```text
bool r = vmops ? vmops->SaveSnapshot(name) : core.SaveShapshot(name);
if (r)
    statusdisplay.Show(...);
else
    statusdisplay.Show(...);
```

This replaces only:

```text
if (core.SaveShapshot(name))
```

## Preserved Behavior

The following remain unchanged:

- `GetSnapshotName(name, n)`
- success/failure status display calls
- `currentsnapshot = n`
- `snapshotchanged = true`
- existing `SaveShapshot` spelling in `WinCore`
- snapshot format and `WinCore` implementation
- snapshot load path

## Intentionally Not Changed

- `WinUI::LoadSnapshot()` still calls direct `core.LoadShapshot(...)`.
- `VMOperations::SaveSnapshot()` implementation was not changed.
- `VMOperations::LoadSnapshot()` implementation was not changed.
- No project files changed.
- No string literal or resource text changed.
- No disk/tape/sound/lifecycle/monitor command path changed.

## Local Verification

Local checks:

```text
git diff --check
rg -n "SaveShapshot|SaveSnapshot\\(" src/win32/ui.cpp src/win32/vmops.h src/win32/vmops.cpp
```

Expected result:

- `WinUI::SaveSnapshot()` uses `vmops->SaveSnapshot(name)` with direct core
  fallback.
- `WinUI::LoadSnapshot()` remains unchanged.
- `VMOperations::SaveSnapshot()` still delegates to `core->SaveShapshot(path)`.

MSVC/VC8 build was not run locally because this WSL environment does not
provide Visual Studio.

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
- sound OK
- snapshot save succeeds
- snapshot load succeeds
- game resumes correctly after load
- clean shutdown
- no new warning dialog or crash

## User-Side Verification Result

User-side verification after commit:

- `892ca77` `Route WinUI snapshot save through VM operations`

Verified:

- VS2008 / VC8 Express `Release|Win32` rebuild: OK
- snapshot save/load runtime check: OK

Note:

- A temporary beep sound anomaly was observed.
- Reproducibility is unconfirmed.
- This step did not change sound paths, but the observation should be kept in
  the report before proceeding further into sound-related boundaries.

## Next Safe Step

After user-side verification, the next small snapshot step is:

```text
Phase 5 WinCore/WinUI operation boundary step 22 を小さく実行しろ。
WinUI::LoadSnapshot の core.LoadShapshot(...) 2 箇所だけを
vmops 経由の LoadSnapshot wrapper に移せ。
OpenDiskImage、diskinfo、status display、currentsnapshot、
WinCore/VMOperations 実装、disk/tape/sound/lifecycle/monitor 変更は禁止。
fallback は維持し、完了後 report を出せ。
```
