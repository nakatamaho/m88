# Phase 5 WinCore/WinUI Operation Boundary Step 22 Report

## Scope

- Route only `WinUI::LoadSnapshot()` to `VMOperations` via fallback form.
- Keep logic and behavior unchanged for:
  - disk handling and multi-disk selection
  - status output
  - snapshot bookkeeping
  - WinCore/VMOperations internals
- Do not touch `project` files.

## Baseline

- Previous pushed commit before this step:
  - `1754ad9` `Record snapshot save/load verification`
- Previous local state:
  - `src/win32/ui.cpp` already had `SaveSnapshot` through `VMOperations` with core fallback.
  - `LoadSnapshot` still used direct `core.LoadShapshot(...)` in 2 places.
- Local MSVC/VC8 build is not available in this environment.
- Existing untracked generated dirs left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Change

In `src/win32/ui.cpp`, inside `WinUI::LoadSnapshot(int n)`:

- `r = core.LoadShapshot(name, diskinfo[0].filename);`
- `r = core.LoadShapshot(name, 0);`

were replaced with:

- `r = vmops ? vmops->LoadSnapshot(name, diskinfo[0].filename) : core.LoadShapshot(name, diskinfo[0].filename);`
- `r = vmops ? vmops->LoadSnapshot(name, 0) : core.LoadShapshot(name, 0);`

No other statements were modified.

## Verification Notes

- `rg -n "LoadShapshot\(" src/win32/ui.cpp` now shows only the two fallback forms above.
- `git diff --check` expected to be clean for whitespace/content-formatting.
- No runtime/build verification executed in this environment.
