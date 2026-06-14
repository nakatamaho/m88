# Phase 5 WinCore/WinUI Operation Boundary Step 27 Inventory

## Scope

- Inventory-only step after Step26.
- Re-check remaining direct `core.*` usages in `src/win32/ui.cpp`.
- No implementation in this step.

## Baseline

- Previous pushed state:
  - `586fd62` `Route PCM command through VMOperations sound handle`
- User-side VC2008 runtime verification has been confirmed in Step26 (all green).
- Existing untracked generated directories remain:
  - `cdif/debug/`
  - `diskdrv/debug/`
- Verification environment: WSL (local build execution for VC2008 not available here).

## Current `core` Direct Call Map (`src/win32/ui.cpp`)

### A) Lifecycle control (not yet migrated)

- `core.Init(this, hwnd, &draw, diskmgr, &keyif, &winconfig, tapemgr)`
- `core.Wait(false)`
- `core.Reset()`
- `core.Cleanup()`

### B) Monitor / wiring (mixed owner)

- `opnmon.Init(core.GetOPN1(), core.GetSound())`
- `core.GetSound()->SetSoundMonitor(&opnmon)`
- local read: `OPNIF* opn = core.GetOPN1();` in cleanup path

### C) Config/reset flow

- `core.ApplyConfig(&config)` (in `ApplyConfig()` path and `Reset()` path)
- `core.Reset()` (already listed in lifecycle)

### D) Volume

- `core.SetVolume((PC8801::Config*) c)` in `M88ChangeVolume()`

### E) Commented legacy code

- `core.ActivateMouse` / `core.SetGUIFlag` references are inside comments and/or debug comments.
- These are not runtime calls but should be excluded from current migration scope unless code is re-enabled.

## Safety notes

- Remaining direct calls are concentrated in lifecycle + monitor + config/volume paths, which were intentionally left out of Step26.
- Read-only menu-state migration has already been handled in earlier steps via vmops wrappers.
- Snapshot and snapshot-load/save paths were moved to vmops in Step25.
- PCM command path migrated to vmops sound in Step26.

## Next Candidate Order (low-risk)

1. Inventory-confirmed, but defer: `ApplyConfig` / `Reset` call sites (core ownership and lifecycle coupling remains active).
2. `SetVolume` migration only after command path and lifecycle ownership are explicitly planned.
3. Monitor/sound wiring remains a higher-risk path due to `WinSound` / `OPN1` initialization timing.

