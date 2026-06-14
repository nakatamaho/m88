# Phase 5 WinCore/WinUI Operation Boundary Step 9 Report

## Scope

- Migrate exactly one `WinUI::WmInitMenu` read-only capability check through `VMOperations`.
- Add only `VMOperations::IsN80Supported()`.
- Replace only the `core.IsN80Supported()` call for `IDM_N80MODE`.
- Do not change disk, tape, snapshot, config, sound, or monitor call sites.
- Do not change `WinCore`, `DiskManager`, or `TapeManager` implementations.

## Baseline

- Pushed commit:
  - `2405371` `Inventory remaining WinUI core calls`
- Current verified state:
  - `VMOperations` is allocated and bound in `WinUI::InitM88`
  - `WinUI::WmTimer` routes `GetExecCount` through `vmops`
  - user-side VS2008 / VC8 Express `Release|Win32` build passed after `559bc91`
  - window title fps/MHz update passed after `559bc91`
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes

`src/win32/vmops.h`:

```text
bool IsN80Supported();
```

`src/win32/vmops.cpp`:

```text
bool VMOperations::IsN80Supported()
{
	return core ? core->IsN80Supported() : false;
}
```

`src/win32/ui.cpp`:

```text
core.IsN80Supported()
```

was replaced in the `IDM_N80MODE` menu enable check with:

```text
vmops ? (vmops->IsN80Supported() ? MF_ENABLED : MF_GRAYED)
      : (core.IsN80Supported() ? MF_ENABLED : MF_GRAYED)
```

## Why This Call

`IsN80Supported` is a read-only capability check.

It only controls the enabled/gray state of the N80 mode menu item when a menu opens.

It does not affect:

- disk state
- tape state
- snapshot state
- config persistence
- sound implementation
- monitor/debug implementation
- VM reset or lifecycle

## Fallback

The `WinUI` call keeps a defensive fallback to the existing direct `core` path if `vmops` is null.

This matches the previous behavior in abnormal lifecycle cases while proving the normal `vmops` path.

## Intentionally Not Changed

- `core.IsN80V2Supported()` remains direct.
- `core.IsCDSupported()` remains direct.
- No disk calls migrated.
- No tape calls migrated.
- No snapshot calls migrated.
- No config calls migrated.
- No sound calls migrated.
- No monitor/debug calls migrated.
- No `WinCore`, `DiskManager`, or `TapeManager` implementation changed.
- No project files changed.

## Local Verification

Local checks:

```text
git diff --check
rg -n "IsN80Supported|IsN80V2Supported|IsCDSupported|vmops" src/win32/ui.cpp src/win32/vmops.h src/win32/vmops.cpp
```

Results:

- `git diff --check` passed.
- Source diff is limited to `VMOperations::IsN80Supported` and one `WinUI::WmInitMenu` call site.
- `IsN80V2Supported` and `IsCDSupported` remain direct to `core`.
- Local MSVC/VC8 build was not run because this WSL environment does not provide Visual Studio.

## User-Side Verification Request

Recommended:

```text
tools\windows\build_vc2008.cmd Release
```

Then verify:

- writetag CRC appears
- M88 launch
- open menu and confirm N80 mode enable/gray state is sane
- D88 game launch
- disk access
- sound
- snapshot save/load
- clean shutdown
- no new warning dialog or crash

## Next Safe Step

If this builds and runs, the next similar migration can be:

```text
core.IsN80V2Supported()
```

Keep it as a separate small step.
