# Phase 5 WinCore/WinUI Operation Boundary Step 24 Report

## Scope

- Migrate `WinUI::WmInitMenu` read-only capability/state queries from fallback forms to `VMOperations`-oriented access.
- Keep snapshot/load/save, config/apply, lifecycle, monitor, and mutating sound paths unchanged.
- Small implementation scope: no project-file changes.

## Baseline

- `WinUI::WmInitMenu` still had read-only menu-state reads via `core.*` fallback.
- `VMOperations` already had wrappers available for the moved paths.
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Changes

In `src/win32/ui.cpp`:

- `WinUI::WmTimer`
  - `int icount = vmops ? vmops->GetExecCount() : core.GetExecCount();`
  - changed to `int icount = vmops ? vmops->GetExecCount() : 0;`
- `WinUI::WmInitMenu`
  - Removed remaining `core` fallback by routing to `vmops` wrappers:
    - `vmops->IsN80Supported()`
    - `vmops->IsN80V2Supported()`
    - `vmops->IsCDSupported()`
    - `vmops->IsSoundDumping()`
    - `vmops->GetCPU1DumpState()`
    - `vmops->GetCPU2DumpState()`

No other behavior or call paths were modified.

## Preserved / Intentionally Not Changed

- snapshot save/load, `core.Init`, `core.Reset`, `core.Cleanup`
- monitor initialization/wiring and mutating sound paths (`DumpBegin`, `DumpEnd`, `SetVolume`)
- `WinCore` implementation and `VMOperations` implementation

## Runtime Verification

- Command: `tools\\windows\\build_vc2008.cmd Release`
- Result:
  - writetag CRC: output present
  - M88 起動: OK
  - メニュー open: OK
  - D88ゲーム / disk access: OK
  - 音: OK
  - snapshot save/load: OK
  - clean shutdown: OK
  - 新規 warning/dialog/crash: none
- Final: **all green**
