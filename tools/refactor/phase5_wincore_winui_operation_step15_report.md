# Phase 5 WinCore/WinUI Operation Boundary Step 15 Report

## Scope

- Migrate only the CPU dump read-only menu state checks in `WinUI::WmInitMenu` through `VMOperations`.
- Add only:
  - `VMOperations::GetCPU1DumpState()`
  - `VMOperations::GetCPU2DumpState()`
- Preserve the existing `GetDumpState()` tri-state values.
- Do not change CPU dump toggle behavior.
- Do not change sound, disk, tape, snapshot, config, or monitor initialization.

## Baseline

- Previous implementation commits:
  - `8099f28` `Route PCM dump menu state through VM operations`
  - `530b3b2` `Write PCM dumps beside M88 executable`
  - `b31eea3` `Record PCM dump menu verification`
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Changes

`src/win32/vmops.h`:

```text
int GetCPU1DumpState();
int GetCPU2DumpState();
```

`src/win32/vmops.cpp`:

```text
int VMOperations::GetCPU1DumpState()
{
	return core ? core->GetCPU1()->GetDumpState() : -1;
}

int VMOperations::GetCPU2DumpState()
{
	return core ? core->GetCPU2()->GetDumpState() : -1;
}
```

`src/win32/ui.cpp`:

- `IDM_DUMPCPU1` enable/check state now reads through `vmops` when available.
- `IDM_DUMPCPU2` enable/check state now reads through `vmops` when available.
- Existing direct `core` fallback remains for abnormal lifecycle cases.

## Tri-State Preservation

The existing menu logic depends on the integer state:

- `-1`: dump unsupported, menu item disabled.
- `0`: dump supported and off, menu item enabled and unchecked.
- `1`: dump supported and on, menu item enabled and checked.

The wrappers return the existing `GetDumpState()` value unchanged.

If `vmops` is not bound, the wrapper returns `-1`, but `WinUI` keeps the existing direct `core` fallback.

## Intentionally Not Changed

- No CPU dump toggle or logging command path changed.
- No CPU implementation changed.
- No sound calls changed.
- No disk calls changed.
- No tape calls changed.
- No snapshot calls changed.
- No config calls changed.
- No monitor initialization changed.
- No project files changed.

## Local Verification

Local checks:

```text
git diff --check
rg -n "GetCPU1DumpState|GetCPU2DumpState|GetDumpState|IDM_DUMPCPU|vmops" src/win32/ui.cpp src/win32/vmops.h src/win32/vmops.cpp
```

Results:

- `git diff --check` passed.
- Source diff is limited to the CPU dump state wrappers and `WinUI::WmInitMenu` CPU dump menu state call sites.
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
- `Dump CPU1` enable/gray and check state remain as before
- `Dump CPU2` enable/gray and check state remain as before
- D88 game launch
- disk access
- sound OK
- snapshot save/load
- clean shutdown
- no new warning dialog or crash

## User-Side Verification Result

User-side verification passed after commit:

- `1fc838e` `Route CPU dump menu state through VM operations`

Verified:

- VS2008 / VC8 Express `Release|Win32` rebuild: OK
- writetag CRC appears: OK
- M88 launch: OK
- open menu: OK
- `Dump CPU1`: gray, same as before
- `Dump CPU2`: gray, same as before
- gray reason:
  - `Release|Win32` uses the `Z80_x86` backend.
  - `Z80_x86::GetDumpState()` returns `-1`.
  - `-1` means dump unsupported, so the menu item is disabled/gray.
- result: pass because this matches the previous behavior
- D88 game launch: OK
- disk access: OK
- sound: OK
- snapshot save/load: OK
- clean shutdown: OK
- new warning dialog or crash: none

## Next Safe Step

After this, the low-risk `WmInitMenu` read-only `core.*` migrations are effectively complete.

The next step should be an inventory or design step before touching higher-risk areas such as:

- `ApplyConfig`
- `Reset`
- snapshot save/load call sites
- sound mutating operations
- monitor initialization
- lifecycle ownership
