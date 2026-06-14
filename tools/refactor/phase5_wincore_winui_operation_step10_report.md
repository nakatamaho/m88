# Phase 5 WinCore/WinUI Operation Boundary Step 10 Report

## Scope

- Migrate exactly one `WinUI::WmInitMenu` read-only capability check through `VMOperations`.
- Add only `VMOperations::IsN80V2Supported()`.
- Replace only the `core.IsN80V2Supported()` call for `IDM_N80V2MODE`.
- Do not change disk, tape, snapshot, config, sound, or monitor call sites.
- Do not change `WinCore`, `DiskManager`, or `TapeManager` implementations.

## Baseline

- Previous implementation commit:
  - `bf16107` `Route N80 support check through VM operations`
- Step 9 user-side verification passed:
  - VS2008 / VC8 Express `Release|Win32` build
  - M88 launch
  - menu open
  - N80 mode enable/gray state same as before
  - D88 game launch
  - disk access
  - sound
  - snapshot save/load
  - clean shutdown
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes

`src/win32/vmops.h`:

```text
bool IsN80V2Supported();
```

`src/win32/vmops.cpp`:

```text
bool VMOperations::IsN80V2Supported()
{
	return core ? core->IsN80V2Supported() : false;
}
```

`src/win32/ui.cpp`:

```text
core.IsN80V2Supported()
```

was replaced in the `IDM_N80V2MODE` menu enable check with:

```text
vmops ? (vmops->IsN80V2Supported() ? MF_ENABLED : MF_GRAYED)
      : (core.IsN80V2Supported() ? MF_ENABLED : MF_GRAYED)
```

## Why This Call

`IsN80V2Supported` is a read-only capability check.

It only controls the enabled/gray state of the N80V2 mode menu item when a menu opens.

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

This matches the previous behavior in abnormal lifecycle cases while proving another normal `vmops` path.

## Intentionally Not Changed

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
- Source diff is limited to `VMOperations::IsN80V2Supported` and one `WinUI::WmInitMenu` call site.
- `IsCDSupported` remains direct to `core`.
- Local MSVC/VC8 build was not run because this WSL environment does not provide Visual Studio.

## User-Side Verification Request

Recommended:

```text
tools\windows\build_vc2008.cmd Release
```

Then verify:

- writetag CRC appears
- M88 launch
- open menu and confirm N80V2 mode enable/gray state is sane
- D88 game launch
- disk access
- sound
- snapshot save/load
- clean shutdown
- no new warning dialog or crash

## Next Safe Step

If this builds and runs, the next similar migration can be:

```text
core.IsCDSupported()
```

Keep it as a separate small step.
