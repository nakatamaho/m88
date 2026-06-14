# Phase 5 WinCore/WinUI Operation Boundary Step 11 Report

## Scope

- Migrate exactly one `WinUI::WmInitMenu` read-only capability check through `VMOperations`.
- Add only `VMOperations::IsCDSupported()`.
- Replace only the `core.IsCDSupported()` call for `IDM_N88V2CD`.
- Do not change disk, tape, snapshot, config, sound, or monitor call sites.
- Do not change `WinCore`, `DiskManager`, or `TapeManager` implementations.

## Baseline

- Previous implementation commits:
  - `bf16107` `Route N80 support check through VM operations`
  - `64caa7f` `Route N80V2 support check through VM operations`
- Step 10 user-side verification passed:
  - VS2008 / VC8 Express `Release|Win32` build
  - M88 launch
  - menu open
  - N80V2 mode check passed
  - `N88-V2(CD) mode` exists and is gray/disabled in the tested state
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
bool IsCDSupported();
```

`src/win32/vmops.cpp`:

```text
bool VMOperations::IsCDSupported()
{
	return core ? core->IsCDSupported() : false;
}
```

`src/win32/ui.cpp`:

```text
core.IsCDSupported()
```

was replaced in the `IDM_N88V2CD` menu enable check with:

```text
vmops ? (vmops->IsCDSupported() ? MF_ENABLED : MF_GRAYED)
      : (core.IsCDSupported() ? MF_ENABLED : MF_GRAYED)
```

## Why This Call

`IsCDSupported` is a read-only capability check.

It only controls the enabled/gray state of the `N88-V2(CD) mode` menu item when a menu opens.

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

This matches the N80 and N80V2 migration pattern and preserves the previous abnormal lifecycle behavior.

## Intentionally Not Changed

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
- Source diff is limited to `VMOperations::IsCDSupported` and one `WinUI::WmInitMenu` call site.
- Local MSVC/VC8 build was not run because this WSL environment does not provide Visual Studio.

## User-Side Verification Request

Recommended:

```text
tools\windows\build_vc2008.cmd Release
```

Then verify:

- writetag CRC appears
- M88 launch
- open menu
- `N88-V2(CD) mode` still exists
- `N88-V2(CD) mode` enable/gray state remains as before
- D88 game launch
- disk access
- sound
- snapshot save/load
- clean shutdown
- no new warning dialog or crash

## Next Safe Step

If this builds and runs, continue with another isolated read-only `WinUI::WmInitMenu` candidate or stop to inventory remaining `core.*` calls again before migrating broader operations.
