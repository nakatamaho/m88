# Phase 5 WinCore/WinUI Operation Boundary Step 25 Report

## Scope

- Small implementation step after Step24.
- Replace remaining snapshot operations in `src/win32/ui.cpp` that still route to `core` with `vmops`-oriented calls only.
- Keep mutation paths, monitor wiring, and lifecycle control unchanged.

## Baseline

- Previous pushed state:
  - `d995f3e` `Record step24 VC2008 runtime verification`
- Existing untracked generated directories left unchanged:
  - `cdif/debug/`
  - `diskdrv/debug/`
- VC2008 runtime verification is outside this WSL environment.

## Change

### `src/win32/ui.cpp`

- `WinUI::SaveSnapshot(int n)`
  - `bool r = vmops ? vmops->SaveSnapshot(name) : core.SaveShapshot(name);`
  - changed to `bool r = vmops ? vmops->SaveSnapshot(name) : false;`

- `WinUI::LoadSnapshot(int n)`
  - first branch `vmops ? vmops->LoadSnapshot(name, diskinfo[0].filename) : core.LoadShapshot(name, diskinfo[0].filename)`
  - changed to `vmops ? vmops->LoadSnapshot(name, diskinfo[0].filename) : false`

  - second branch `vmops ? vmops->LoadSnapshot(name, 0) : core.LoadShapshot(name, 0)`
  - changed to `vmops ? vmops->LoadSnapshot(name, 0) : false`

## Preservation Policy

- No snapshot format/layout changes.
- No `WinCore` / `VMOperations` implementation changes.
- No changes to config/reset/monitor/disk/tape/sound lifecycle paths.
- Runtime side effects are unchanged except fallback behavior when `vmops` is unavailable.

## Notes

- This step removes the last direct `core` dependency in snapshot call sites.
- When `vmops` is null, snapshot processing now reports failure as intended (safe no-op).
- User-side VC2008 verification is still required to confirm behavior under actual runtime:
  - `tools\\windows\\build_vc2008.cmd Release`
  - open menu / startup / snapshot save/load checks.

