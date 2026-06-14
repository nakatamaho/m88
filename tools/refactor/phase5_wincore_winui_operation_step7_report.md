# Phase 5 WinCore/WinUI Operation Boundary Step 7 Report

## Scope

- Migrate exactly one low-risk `WinUI` read-only operation through `VMOperations`.
- Replace only the `core.GetExecCount()` call in `WinUI::WmTimer`.
- Do not change disk, tape, snapshot, or config call sites.
- Do not change `WinCore`, `DiskManager`, or `TapeManager` implementations.
- Do not change VM logic.

## Baseline

- Pushed commit:
  - `c0680af` `Record VM operations lifecycle verification`
- Step 6 user-side verification passed:
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

```text
core.GetExecCount()
```

was replaced with:

```text
vmops ? vmops->GetExecCount() : core.GetExecCount()
```

This is in `WinUI::WmTimer`, where the value is used for the window title report.

## Why This Call

`GetExecCount` is read-only and does not affect:

- disk state
- tape state
- snapshot state
- config state
- VM reset
- audio/video/input logic

It is a low-risk first call migration to prove that `WinUI` can use the bound `VMOperations` facade.

## Fallback

The call uses a defensive fallback:

```text
vmops ? vmops->GetExecCount() : core.GetExecCount()
```

`vmops` should be allocated and bound after successful `InitM88`, but the fallback keeps behavior identical if the timer is reached while `vmops` is null.

## Intentionally Not Changed

- No disk calls migrated.
- No tape calls migrated.
- No snapshot calls migrated.
- No config calls migrated.
- No monitor initialization changed.
- No `core.GetSound()` calls migrated.
- No `WinCore`, `DiskManager`, or `TapeManager` implementation changed.
- No project files changed.

## Local Verification

Local checks:

```text
git diff --check
git diff -- src/win32/ui.cpp
rg -n "GetExecCount|vmops|diskmgr->|tapemgr->|SaveShapshot|LoadShapshot" src/win32/ui.cpp
```

Results:

- `git diff --check` passed.
- Source diff is limited to one `WinUI::WmTimer` line.
- `diskmgr->*`, `tapemgr->*`, snapshot, and config call sites remain unchanged.
- Local MSVC/VC8 build was not run because this WSL environment does not provide Visual Studio.

## User-Side Verification

User-side verification after commit `559bc91`:

```text
VS2008 / VC8 Express Release|Win32 build: passed
```

Runtime smoke:

- window title fps/MHz update: passed

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

Also watch the window title / report update, because this step changes the path used for `GetExecCount`.

## Next Safe Step

If this builds and runs, the next low-risk migration can be another read-only `core` call, not disk/tape/snapshot/config.

Candidate:

```text
core.GetSound()->IsDumping()
```

However, sound is more visible than `GetExecCount`, so a design/inventory pass for remaining safe `core` read-only calls may be preferable before migrating more calls.
