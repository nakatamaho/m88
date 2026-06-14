# Phase 5 WinCore/WinUI Operation Boundary Step 24 Report

## Scope

- Move WmInitMenu read-only capability/state checks from direct `core.*` fallback to `VMOperations`-only access.
- Keep menu state behavior unchanged (enable/checked semantics).
- Do not touch snapshot/load/save, apply config/reset, lifecycle, disk/tape, sound mutating paths.

## Baseline

- Previous local state: Step 22 and Step 23 already completed and reported.
- `WmInitMenu` still had `core.*` fallback expressions for menu capability checks:
  - `IsN80Supported`, `IsN80V2Supported`, `IsCDSupported`
  - `GetSound()->IsDumping`
  - `GetCPU1()->GetDumpState`, `GetCPU2()->GetDumpState`

## Change

In `src/win32/ui.cpp` (`WinUI::WmInitMenu`), replaced the fallback forms with direct `vmops` wrapper calls:

- `EnableMenuItem(... N80 )`:
  - from `vmops ? vmops->IsN80Supported() ? ... : core.IsN80Supported() ? ...`
  - to `vmops->IsN80Supported() ? ...`
- `EnableMenuItem(... N80V2 )`:
  - from `vmops ? vmops->IsN80V2Supported() ? ... : core.IsN80V2Supported() ? ...`
  - to `vmops->IsN80V2Supported() ? ...`
- `EnableMenuItem(... N88V2CD )`:
  - from `vmops ? vmops->IsCDSupported() ? ... : core.IsCDSupported() ? ...`
  - to `vmops->IsCDSupported() ? ...`
- `CheckMenuItem(... IDM_RECORDPCM )`:
  - from `vmops ? vmops->IsSoundDumping() : core.GetSound()->IsDumping()`
  - to `vmops->IsSoundDumping()`
- `EnableMenuItem/CheckMenuItem` for `IDM_DUMPCPU1`, `IDM_DUMPCPU2`:
  - from `vmops ? vmops->GetCPU*DumpState() : core.GetCPU*()->GetDumpState()`
  - to `vmops->GetCPU*DumpState()`

No other `WmInitMenu` behavior was modified.

## Preserved Elements

- `config`-based checks and all menu item wiring.
- `opnmon/memmon/basmon` debug monitor state handling.
- snapshot/state/lifecycle/sound mutating call paths.
- No `vmops` initialization logic changed in this step.

## Local Checks

- `rg -n "core\.IsN80Supported|core\.IsN80V2Supported|core\.IsCDSupported|core\.GetSound\(\)->IsDumping|core\.GetCPU1\(\)->GetDumpState|core\.GetCPU2\(\)->GetDumpState" src/win32/ui.cpp`
- Expected result: no matches in `WinUI::WmInitMenu`.

A direct MSVC build was not executed in this WSL environment.

## User-Side Verification Request

- `tools\windows\build_vc2008.cmd Release`
- Confirm:
  - writetag CRC appears
  - M88 起動
  - D88 ゲーム起動
  - disk access
  - 音
  - snapshot save/load
  - clean shutdown
  - menu opens and N80 / N80V2 / CD / PCM / Dump CPU1/CPU2 states match legacy behavior
  - no new warning/dialog/crash
