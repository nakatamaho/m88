# Phase 5 WinCore/WinUI Operation Boundary Step 5 Report

## Scope

- Convert `VMOperations` from owning `WinCore` to referencing `WinCore*`.
- Add `Bind`, `Unbind`, and `IsBound`.
- Keep `VMOperations::Init()` as a compatibility entry and route it toward `Bind`.
- Do not allocate `vmops` in `WinUI`.
- Do not replace existing `WinCore core` call sites.
- Do not migrate disk, tape, snapshot, or config call sites.
- Do not change runtime logic.

## Baseline

- Pushed commit:
  - `2859169` `Design VM operations reference ownership`
- Previously verified state:
  - `WinUI` holds `VMOperations* vmops`
  - `vmops` is initialized to `0`
  - `vmops` is not allocated
  - no call site uses `vmops`
  - user-side VS2008 / VC8 Express `Release|Win32` build and runtime smoke passed after `0ab7efc`
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes

`src/win32/vmops.h`:

- changed private member from:

```text
WinCore core;
```

to:

```text
WinCore* core;
```

- added:

```text
void Bind(WinCore* core, DiskManager* diskmgr, TapeManager* tapemgr);
void Unbind();
bool IsBound() const;
```

`src/win32/vmops.cpp`:

- constructor now initializes `core` to `0`
- `Bind` stores non-owning pointers
- `Unbind` clears all pointers
- `Cleanup` calls `Unbind` and returns `true`
- `Start`, `Stop`, `Reset`, `ApplyConfig`, `SaveSnapshot`, `LoadSnapshot`, `GetSound`, `GetExecCount`, `Lock`, `Unlock`, and `QueryIF` now guard `core`
- `DiskManager` and `TapeManager` wrappers remain non-owning pointer wrappers

## `Init()` Compatibility

`VMOperations::Init()` was kept, but it no longer creates or initializes a `WinCore`.

Current behavior:

```text
Bind(0, disk, tape);
return false;
```

Reason:

- The active `WinCore` must remain owned and initialized by `WinUI`.
- Calling `WinCore::Init` from `VMOperations` would reintroduce a second VM lifecycle path.
- `Init()` is not used by any current call site.
- Keeping the symbol avoids an API removal in the same step.

Future direction:

- later call sites should use `Bind(&core, diskmgr, tapemgr)`
- once no code depends on `Init()`, consider deleting it in a separate approved cleanup

## Intentionally Not Changed

- `WinUI` still does not allocate `vmops`.
- `WinUI` still does not call `Bind`.
- Existing `WinCore core` remains in `WinUI`.
- No `core.*` call sites were replaced.
- No `diskmgr->*` call sites were replaced.
- No `tapemgr->*` call sites were replaced.
- No snapshot save/load call sites were replaced.
- No config load/save/apply behavior was changed.
- No project files were changed.

## Local Verification

Local checks:

```text
git diff --check
rg -n "VMOperations|vmops|\.Init\(" src/win32/ui.cpp src/win32/ui.h src/win32/vmops.cpp src/win32/vmops.h
```

Results:

- `git diff --check` passed.
- `WinUI` still only holds `VMOperations* vmops` and initializes it to `0`.
- No new `vmops` call sites were added.
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

If this builds and runs, the next small implementation can allocate and bind `VMOperations` without migrating call sites:

```text
Phase 5 WinCore/WinUI operation boundary step 6 を小さく実行しろ。
WinUI::InitM88 で VMOperations を allocate して Bind(&core, diskmgr, tapemgr) し、
WinUI::CleanupM88 で Unbind/delete しろ。
既存 core/diskmgr/tapemgr 呼び出し元置換は禁止。
disk/tape/snapshot/config 呼び出し元変更は禁止。
ロジック変更は禁止。
完了後 report を出せ。
```
