# Phase 5 WinCore/WinUI Operation Boundary Step 22 Report

## Scope

- Route only `WinUI::LoadSnapshot()` calls to `VMOperations` through fallback form.
- Keep behavior unchanged for snapshot bookkeeping, error display, disk/image selection, and core/vmops implementations.
- Do not touch project files.

## Baseline

- Snapshot save path had already been routed to `VMOperations`.
- `WinUI::LoadSnapshot()` still had two direct `core.LoadShapshot(...)` calls.
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Change

In `src/win32/ui.cpp`, inside `WinUI::LoadSnapshot(int n)`:

- `r = core.LoadShapshot(name, diskinfo[0].filename)`
- `r = core.LoadShapshot(name, 0)`

were changed to:

- `r = vmops ? vmops->LoadSnapshot(name, diskinfo[0].filename) : core.LoadShapshot(name, diskinfo[0].filename)`
- `r = vmops ? vmops->LoadSnapshot(name, 0) : core.LoadShapshot(name, 0)`

No other `WinUI` logic changed.

## Verification Notes

- `rg -n "LoadShapshot\(" src/win32/ui.cpp` now shows only routing through `vmops` with fallback to `core`.
- No `git diff --check` issues in this step.
- Runtime/build verification not executed in this environment (VC build is external).
