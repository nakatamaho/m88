# Phase 5 WinCore/WinUI Operation Boundary Step 23 Inventory

## Scope

- Inventory remaining `core.*` call sites in `src/win32/ui.cpp` after Step 22.
- Keep scope to WinUI call-sites only and do not change implementation.
- Keep `disk/tape/snapshot/config/sound implementation` constraints for next steps.

## Search Method

```text
rg -n "\bcore\." src/win32/ui.cpp
```

## Current Remaining Core Call Sites

### Lifecycle / VM control

- `src/win32/ui.cpp:129` `core.Init(this, hwnd, &draw, diskmgr, &keyif, &winconfig, tapemgr)`
- `src/win32/ui.cpp:152` `core.Wait(false)`
- `src/win32/ui.cpp:165` `core.Reset()`
- `src/win32/ui.cpp:190` `core.Cleanup()`

### VM / sound object access

- `src/win32/ui.cpp:136` `opnmon.Init(core.GetOPN1(), core.GetSound())`
- `src/win32/ui.cpp:143` `core.GetSound()->SetSoundMonitor(&opnmon)`

### Sound mutating

- `src/win32/ui.cpp:675` `core.GetSound()->IsDumping()`
- `src/win32/ui.cpp:683` `core.GetSound()->DumpBegin(buf)`
- `src/win32/ui.cpp:687` `core.GetSound()->DumpEnd()`
- `src/win32/ui.cpp:1530` `core.SetVolume((PC8801::Config*) c)`

### Read-only VM capability / status (fallback only)

- `src/win32/ui.cpp:836` `core.GetExecCount()`
- `src/win32/ui.cpp:892` `core.IsN80Supported()`
- `src/win32/ui.cpp:894` `core.IsN80V2Supported()`
- `src/win32/ui.cpp:897` `core.IsCDSupported()`
- `src/win32/ui.cpp:911` `core.GetSound()->IsDumping()`
- `src/win32/ui.cpp:913` `core.GetCPU1()->GetDumpState()`
- `src/win32/ui.cpp:914` `core.GetCPU1()->GetDumpState()`
- `src/win32/ui.cpp:915` `core.GetCPU2()->GetDumpState()`
- `src/win32/ui.cpp:916` `core.GetCPU2()->GetDumpState()`

### Snapshot / config fallback branches

- `src/win32/ui.cpp:1857` `core.SaveShapshot(name)`
- `src/win32/ui.cpp:1877` `core.LoadShapshot(name, diskinfo[0].filename)`
- `src/win32/ui.cpp:1881` `core.LoadShapshot(name, 0)`
- `src/win32/ui.cpp:992` `core.ApplyConfig(&config)`
- `src/win32/ui.cpp:1046` `core.ApplyConfig(&config)`

### Optional monitor usage (commented paths)

- `src/win32/ui.cpp:294` `core.ActivateMouse(true)`
- `src/win32/ui.cpp:474` `core.ActivateMouse(!background)`
- `src/win32/ui.cpp:1696` `core.ActivateMouse(false)`
- `src/win32/ui.cpp:1702` `core.ActivateMouse(true)`
- `src/win32/ui.cpp:1818` `core.SetGUIFlag(gui)`

## Notes

- Step 22 has moved both `LoadSnapshot` call sites to `vmops` fallback form.
- Remaining direct `core.*` call sites are concentrated in lifecycle, monitor, sound-mutating, and fallback-state categories.
- Snapshot-related call sites now keep fallback safety while using `VMOperations` path by default.

## Recommended Next Step Candidate

- Continue with read-only migration in `WmInitMenu`-adjacent wrappers, keeping lifecycle and sound mutation paths for later phases.
