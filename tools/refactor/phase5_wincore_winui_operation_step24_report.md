# Phase 5 WinCore/WinUI Operation Boundary Step 24 Report

## Scope

- Migrate `WinUI::WmInitMenu` read-only capability/state queries from fallback forms to `VMOperations`-oriented access.
- Preserve menu behavior (`MF_ENABLED` / `MF_CHECKED`) semantics.
- Keep snapshot/load/save, config/apply, lifecycle, monitor and mutating sound paths unchanged.

## Baseline

- Wm menu still had read-only calls reachable through `core.*` fallback combinations.
- `VMOperations` already had wrappers and lifecycle ownership for the moved paths.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes

In `src/win32/ui.cpp`:

- `WinUI::WmInitMenu` capability/state read queries were updated to direct `vmops` wrapper calls:
  - `vmops->IsN80Supported()`
  - `vmops->IsN80V2Supported()`
  - `vmops->IsCDSupported()`
  - `vmops->IsSoundDumping()`
  - `vmops->GetCPU1DumpState()`
  - `vmops->GetCPU2DumpState()`
- `WinUI::WmTimer` readout remains guard-safe with `vmops ? vmops->GetExecCount() : 0`.

No other behavior or call paths were modified.

## Verification Notes

- `rg -n "core\.IsN80Supported|core\.IsN80V2Supported|core\.IsCDSupported|core\.GetSound\(\)->IsDumping|core\.GetCPU[12]\(\)->GetDumpState" src/win32/ui.cpp`
  - expected: no matches remaining in `WmInitMenu`.
- `git diff --check` expected to be clean for the touched ranges.
- Runtime/build verification not executed in this environment.
